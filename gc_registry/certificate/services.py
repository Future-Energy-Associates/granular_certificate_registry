import datetime
import json
from typing import Any, Callable, Hashable, cast

import pandas as pd
import pytz
from esdbclient import EventStoreDBClient
from sqlalchemy import func
from sqlmodel import Session, SQLModel, desc, or_, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.account.models import Account, AccountWhitelistLink
from gc_registry.certificate.models import (
    GranularCertificateAction,
    GranularCertificateBundle,
    GranularCertificateBundleUpdate,
    IssuanceMetaData,
)
from gc_registry.certificate.schemas import (
    ActionOutcome,
    ActionResult,
    CertificateStatus,
    GranularCertificateActionBase,
    GranularCertificateActionRead,
    GranularCertificateBundleBase,
    GranularCertificateBundleCreate,
    GranularCertificateBundleRead,
    GranularCertificateCancel,
    GranularCertificateCancelStorage,
    GranularCertificateClaim,
    GranularCertificateLock,
    GranularCertificateQuery,
    GranularCertificateReserve,
    GranularCertificateTransfer,
    GranularCertificateWithdraw,
    IssuanceMetaDataBase,
)
from gc_registry.certificate.validation import (
    validate_granular_certificate_bundle,
    validate_imported_granular_certificate_bundle,
)
from gc_registry.core.database import cqrs, db, events
from gc_registry.core.models.base import CertificateActionType
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.meter_data.abstract_meter_client import AbstractMeterDataClient
from gc_registry.device.models import Device
from gc_registry.device.services import (
    create_import_device,
    get_all_devices,
    get_certificate_bundles_by_device_id,
    get_device_by_local_identifier,
)
from gc_registry.logging_config import logger
from gc_registry.storage.schemas import AllocatedStorageRecordUpdate
from gc_registry.storage.services import (
    issue_sdgcs_against_allocated_records,
)
from gc_registry.storage.utils import (
    get_allocated_storage_records_for_storage_record_id,
    get_storage_record_by_device_id_and_interval,
)


def get_certificate_bundles_by_id(
    granular_certificate_bundle_ids: list[int], db_session: Session
) -> list[GranularCertificateBundle]:
    """Get a list of GC Bundles by their IDs.

    Args:
        granular_certificate_bundle_ids (list[int]): The list of GC Bundle IDs
        db_session (Session): The database session

    Returns:
        list[GranularCertificateBundle]: The list of GC Bundles
    """

    stmt: SelectOfScalar = select(GranularCertificateBundle).where(
        GranularCertificateBundle.id.in_(granular_certificate_bundle_ids)  # type: ignore
    )
    granular_certificate_bundles = db_session.exec(stmt).all()

    return granular_certificate_bundles


def split_certificate_bundle(
    granular_certificate_bundle: GranularCertificateBundle
    | GranularCertificateBundleRead,
    size_to_split: int,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> tuple[GranularCertificateBundle, GranularCertificateBundle]:
    """Given a GC Bundle, split it into two child bundles and return them.

    Example operation: a parent bundle with 100 certificates, when passed a
    size_to_split of 25, will return the first child bundle with 25 certificates
    and the second bundle with 75. Each of these will be created separately as
    new bundles, with the same issuance ID of the parent bundle, and the parent
    bundle will be marked as deleted but preserved in the database for audit
    and lineage purposes.

    Args:
        granular_certificate_bundle (GranularCertificateBundle): The parent GC Bundle
        size_to_split (int): The number of certificates to split from
            the parent bundle.

    Returns:
        tuple[GranularCertificateBundle, GranularCertificateBundle]: The two child GC Bundles
    """

    if size_to_split == 0:
        err_msg = "The size to split must be greater than 0"
        logger.error(err_msg)
        raise ValueError(err_msg)
    if size_to_split >= granular_certificate_bundle.bundle_quantity:
        err_msg = "The size to split must be less than the total certificates in the parent bundle"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Create two child bundles
    granular_certificate_bundle_child_1 = GranularCertificateBundleCreate(
        **granular_certificate_bundle.model_dump()
    )
    granular_certificate_bundle_child_2 = GranularCertificateBundleCreate(
        **granular_certificate_bundle.model_dump()
    )

    # Update the child bundles with the new quantities
    granular_certificate_bundle_child_1.bundle_quantity = size_to_split
    granular_certificate_bundle_child_1.certificate_bundle_id_range_end = (
        granular_certificate_bundle_child_1.certificate_bundle_id_range_start
        + size_to_split
    )
    granular_certificate_bundle_child_1.hash = create_bundle_hash(
        granular_certificate_bundle_child_1, granular_certificate_bundle.hash
    )

    granular_certificate_bundle_child_2.bundle_quantity = (
        granular_certificate_bundle.bundle_quantity - size_to_split
    )
    granular_certificate_bundle_child_2.certificate_bundle_id_range_start = (
        granular_certificate_bundle_child_1.certificate_bundle_id_range_end + 1
    )
    granular_certificate_bundle_child_2.hash = create_bundle_hash(
        granular_certificate_bundle_child_2, granular_certificate_bundle.hash
    )

    # Mark the parent bundle as withdrawn and apply soft delete
    granular_certificate_bundle.certificate_bundle_status = (
        CertificateStatus.BUNDLE_SPLIT
    )
    granular_certificate_bundle.delete(write_session, read_session, esdb_client)  # type: ignore

    # Write the child bundles to the database
    db_granular_certificate_bundle_child_1 = GranularCertificateBundle.create(
        granular_certificate_bundle_child_1, write_session, read_session, esdb_client
    )
    db_granular_certificate_bundle_child_2 = GranularCertificateBundle.create(
        granular_certificate_bundle_child_2, write_session, read_session, esdb_client
    )

    return db_granular_certificate_bundle_child_1[
        0
    ], db_granular_certificate_bundle_child_2[0]  # type: ignore


def create_issuance_id(
    granular_certificate_bundle: GranularCertificateBundleBase,
) -> str:
    return f"{granular_certificate_bundle.device_id}-{granular_certificate_bundle.production_starting_interval}"


def issuance_id_to_device_and_interval(
    issuance_id: str,
) -> tuple[int, datetime.datetime]:
    parts = issuance_id.split("-")
    if len(parts) < 4:
        raise ValueError(f"Invalid issuance ID: {issuance_id}")

    try:
        device_id = int(parts[0])
        interval = datetime.datetime.fromisoformat("-".join(parts[1:]))
    except ValueError:
        raise ValueError(f"Invalid issuance ID: {issuance_id}")

    return device_id, interval


def get_max_certificate_id_by_device_id(
    db_session: Session, device_id: int
) -> int | None:
    """Gets the maximum certificate ID from any bundle for a given device, excluding any withdrawn certificates.

    Args:
        db_session (Session): The database session
        device_id (int): The device ID

    Returns:
        int | None: The maximum certificate ID
    """

    stmt: SelectOfScalar = select(
        func.max(GranularCertificateBundle.certificate_bundle_id_range_end)
    ).where(
        GranularCertificateBundle.device_id == device_id,
        GranularCertificateBundle.certificate_bundle_status
        != CertificateStatus.WITHDRAWN,
    )

    max_certificate_id = db_session.exec(stmt).first()

    if not max_certificate_id:
        return None
    else:
        return int(max_certificate_id)


def get_max_certificate_timestamp_by_device_id(
    db_session: Session, device_id: int
) -> datetime.datetime | None:
    """Gets the maximum certificate timestamp from any bundle for a given device, excluding any withdrawn certificates

    Args:
        db_session (Session): The database session
        device_id (int): The device ID

    Returns:
        datetime.datetime: The maximum certificate timestamp

    """

    stmt: SelectOfScalar = select(
        func.max(GranularCertificateBundle.production_ending_interval)
    ).where(
        GranularCertificateBundle.device_id == device_id,
        GranularCertificateBundle.certificate_bundle_status
        != CertificateStatus.WITHDRAWN,
    )

    max_certificate_timestamp = db_session.exec(stmt).first()

    if not max_certificate_timestamp:
        return None
    else:
        return max_certificate_timestamp


def issue_certificates_by_device_in_date_range(
    device: Device,
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
    issuance_metadata_id: int,
    meter_data_client: AbstractMeterDataClient,
) -> list[SQLModel] | None:
    """Issue certificates for a device using the following process.
    1. Get max timestamp already issued for the device
    2. Get the meter data for the device for the given period
    3. Map the meter data to certificates
    4. Validate the certificates
    5. Commit the certificates to the database
    Args:
        device (Device): The device
        from_datetime (datetime.datetime): The start of the period
        to_datetime (datetime.datetime): The end of the period
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client
        issuance_metadata_id (int): The issuance metadata ID
        meter_data_client (MeterDataClient, optional): The meter data client.

    Returns:
        list[GranularCertificateBundle]: The list of certificates issued
    """

    # check that date times are in UTC
    if from_datetime.tzinfo is None or to_datetime.tzinfo is None:
        err_msg = "from_datetime and to_datetime must be timezone aware"
        logger.error(err_msg)
        raise ValueError(err_msg)

    if (
        from_datetime.tzinfo != pytz.UTC
        and from_datetime.tzinfo != datetime.timezone.utc
    ) or (
        to_datetime.tzinfo != pytz.UTC and to_datetime.tzinfo != datetime.timezone.utc
    ):
        err_msg = "from_datetime and to_datetime must be in UTC"
        logger.error(err_msg)
        raise ValueError(err_msg)

    if not device.id or not device.local_device_identifier:
        logger.error(f"No device ID or meter data ID for device: {device}")
        return None

    # get max timestamp already issued for the device
    max_issued_timestamp = get_max_certificate_timestamp_by_device_id(
        read_session, device.id
    )

    # check if the device has already been issued certificates for the given period
    if max_issued_timestamp is not None:
        max_issued_timestamp = pd.to_datetime(max_issued_timestamp, utc=True)
        if max_issued_timestamp >= to_datetime:
            logger.info(
                f"Device {device.id} has already been issued certificates for the period {from_datetime} to {to_datetime}"
            )
            return None

        # If max timestamp is after from them use the max timestamp as the from_datetime
        if max_issued_timestamp > from_datetime:
            from_datetime = max_issued_timestamp

    # TODO CAG - this is messy by me, will refactor down the road
    # Also, validation later on assumes the metering data is datetime sorted -
    # can we guarantee this at the meter client level?
    if meter_data_client.NAME == "ManualSubmissionMeterClient":
        meter_data = meter_data_client.get_metering_by_device_in_datetime_range(
            from_datetime, to_datetime, device.id, read_session
        )
    else:
        meter_data = meter_data_client.get_metering_by_device_in_datetime_range(
            from_datetime, to_datetime, device.local_device_identifier
        )

    if not meter_data:
        logger.info(
            f"No meter data retrieved for device: {device.local_device_identifier}"
        )
        return None

    # Map the meter data to certificates
    device_max_certificate_id = get_max_certificate_id_by_device_id(
        read_session, device.id
    )
    if not device_max_certificate_id:
        certificate_bundle_id_range_start = 1
    else:
        certificate_bundle_id_range_start = device_max_certificate_id + 1

    certificates = meter_data_client.map_metering_to_certificates(
        generation_data=meter_data,
        certificate_bundle_id_range_start=certificate_bundle_id_range_start,
        account_id=device.account_id,
        device=device,
        is_storage=device.is_storage,
        issuance_metadata_id=issuance_metadata_id,
    )

    if not certificates:
        err_msg = (
            f"No meter data retrieved for device: {device.local_device_identifier}"
        )
        logger.error(err_msg)
        return None

    if not device_max_certificate_id:
        device_max_certificate_id = 0

    # Validate the certificates
    valid_certificates: list[Any] = []
    for certificate in certificates:
        # get max valid certificate max bundle id
        if valid_certificates:
            device_max_certificate_id = max(
                [v.certificate_bundle_id_range_end for v in valid_certificates]
            )

        if device_max_certificate_id is None:
            err_msg = "Max certificate ID is None"
            logger.error(err_msg)
            raise ValueError(err_msg)

        valid_certificate = validate_granular_certificate_bundle(
            read_session,
            certificate,
            is_storage_device=device.is_storage,
            max_certificate_id=device_max_certificate_id,
        )
        valid_certificate.hash = create_bundle_hash(valid_certificate, nonce="")
        valid_certificate.issuance_id = create_issuance_id(valid_certificate)
        valid_certificates.append(valid_certificate)

        # Because this function is only applied to one device at a time, we can be
        # certain that the highest bundle id range end is from the most recent bundle
        # in this collection
        device_max_certificate_id = valid_certificate.certificate_bundle_id_range_end

    # Batch commit the GC bundles to the database
    created_entities = cqrs.write_to_database(
        valid_certificates,  # type: ignore
        write_session,
        read_session,
        esdb_client,
    )

    return created_entities


def issue_certificates_in_date_range(
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
    issuance_metadata_id: int,
    meter_data_client: AbstractMeterDataClient,
) -> list[SQLModel] | None:
    """Issues certificates for a device using the following process.
    1. Get a list of devices in the registry and their capacities
    2. For each device, get the meter data for the device for the given period
    3. Map the meter data to certificates
    4. Validate the certificates
    5. Commit the certificates to the database

    Args:
        from_datetime (datetime.datetime): The start of the period
        to_datetime (datetime.datetime): The end of the period
        write_session (Session): The database write session
        read_session (Session): The database read session
        issuance_metadata_id (int): The issuance metadata ID
        meter_data_client (MeterDataClient, optional): The meter data client. Defaults to Depends(ElexonClient).

    Returns:
        list[GranularCertificateBundle]: The list of certificates issued

    """

    # Get the devices in the registry
    devices = get_all_devices(read_session)

    if not devices:
        logger.error("No devices found in the registry")
        return None

    # Issue certificates for each device
    certificate_bundles: list[Any] = []
    for device in devices:
        logger.info(f"Issuing certificates for device: {device.id}")

        # Get the meter data for the device
        if not device.local_device_identifier:
            logger.error(f"No meter data ID for device: {device.id}")
            continue

        if not device.id:
            logger.error(f"No device ID for device: {device}")
            continue

        created_entities = issue_certificates_by_device_in_date_range(
            device,
            from_datetime,
            to_datetime,
            write_session,
            read_session,
            esdb_client,
            issuance_metadata_id,
            meter_data_client,
        )
        if created_entities:
            certificate_bundles.extend(created_entities)

    return certificate_bundles


def issue_certificates_metering_integration_for_all_devices_in_date_range(
    from_date: datetime.datetime, to_date: datetime.datetime, metering_client: Any
) -> None:
    """
    Seed the database with all generators data from the given source
    Args:
        client: The client to use to get the data
        from_datetime: The start datetime to get the data from
        to_datetime: The end datetime to get the data to
    """

    _ = db.get_db_name_to_client()
    write_session = db.get_write_session()
    read_session = db.get_read_session()
    esdb_client = events.get_esdb_client()

    # Create issuance metadata for the certificates
    issuance_metadata_dict: dict[Hashable, Any] = {
        "country_of_issuance": "UK",
        "connected_grid_identification": "NESO",
        "issuing_body": "OFGEM",
        "legal_status": "legal",
        "issuance_purpose": "compliance",
        "support_received": None,
        "quality_scheme_reference": None,
        "dissemination_level": None,
        "issue_market_zone": "NESO",
    }

    issuance_metadata_list = IssuanceMetaData.create(
        issuance_metadata_dict,
        write_session,
        read_session,
        esdb_client,
    )

    if not issuance_metadata_list:
        raise ValueError("Could not create issuance metadata")

    issuance_metadata = issuance_metadata_list[0]

    issue_certificates_in_date_range(
        from_date,
        to_date,
        write_session,
        read_session,
        esdb_client,
        issuance_metadata.id,  # type: ignore
        metering_client,
    )


def process_certificate_bundle_action(
    certificate_action: GranularCertificateActionBase,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> GranularCertificateActionRead | None:
    """Process the given certificate action.

    Args:
        certificate_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    Returns:
        GranularCertificateAction: The certificate action processed

    """

    # Action request datetimes are set prior to the operation; action complete datetimes are set
    # using a default factory once the action entity is written to the DB post-completion

    valid_certificate_action = GranularCertificateAction.model_validate(
        certificate_action.model_dump()
    )
    valid_certificate_action.action_request_datetime = datetime.datetime.now(
        tz=datetime.timezone.utc
    )

    certificate_action_functions: dict[str, Callable[..., Any]] = {
        CertificateActionType.TRANSFER: transfer_certificates,
        CertificateActionType.CANCEL: cancel_certificates,
        CertificateActionType.CLAIM: claim_certificates,
        CertificateActionType.WITHDRAW: withdraw_certificates,
        CertificateActionType.LOCK: lock_certificates,
        CertificateActionType.RESERVE: reserve_certificates,
        CertificateActionType.CANCEL_FOR_STORAGE: cancel_certificates_for_storage,
    }

    if valid_certificate_action.action_type not in certificate_action_functions.keys():
        err_msg = f"Action type ({valid_certificate_action.action_type}) not in {certificate_action_functions.keys()}"
        logger.error(err_msg)
        raise ValueError(err_msg)

    action_function: Callable[..., Any] = certificate_action_functions[
        valid_certificate_action.action_type
    ]

    action_result = action_function(
        certificate_action, write_session, read_session, esdb_client
    )

    db_certificate_actions = GranularCertificateAction.create(
        valid_certificate_action, write_session, read_session, esdb_client
    )

    if not db_certificate_actions:
        raise ValueError("Could not create certificate action")

    action_read = GranularCertificateActionRead(
        action_result=action_result, **db_certificate_actions[0].model_dump()
    )

    return action_read


def apply_bundle_quantity_or_percentage(
    certificate_bundles_from_query: list[GranularCertificateBundle],
    certificate_bundle_action: GranularCertificateCancel
    | GranularCertificateTransfer
    | GranularCertificateReserve
    | GranularCertificateClaim
    | GranularCertificateWithdraw
    | GranularCertificateLock,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> list[GranularCertificateBundle]:
    """Apply the bundle quantity or percentage to the certificates from the query.

    For each GC Bundle returned from the query, this function will split the bundle
    if the desired GC quantity or percentage is less than the GC Bundle quantity, otherwise
    it will return the GC Bundle unsplit.

    Args:
        certificate_bundles_from_query (list[GranularCertificateBundle]): The certificates from the query
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    Returns:
        list[GranularCertificateBundle]: The list of certificates to transfer, split if required
                                         such that the quantity of each bundle is equal to or
                                         less than the desired bundle quantity, if provided, or
                                         the percentage of the total certificates in the bundle.

    """
    # Just return the certificates from the query if no quantity or percentage is provided
    if (certificate_bundle_action.certificate_quantity is None) & (
        certificate_bundle_action.certificate_bundle_percentage is None
    ):
        return certificate_bundles_from_query

    certificates_bundles_to_transfer = []

    if certificate_bundle_action.certificate_quantity is not None:
        certificates_bundles_to_split = [
            certificate_bundle_action.certificate_quantity
            for i in range(len(certificate_bundles_from_query))
        ]
    elif certificate_bundle_action.certificate_bundle_percentage is not None:
        certificates_bundles_to_split = [
            int(
                certificate_bundle_action.certificate_bundle_percentage
                * certificate_from_query.bundle_quantity
            )
            for certificate_from_query in certificate_bundles_from_query
        ]

    # Only check the bundle quantity if the query on bundle quantity parameter is provided,
    # otherwise, split the bundle based on the percentage of the total certificates in the bundle
    for idx, granular_certificate_bundle in enumerate(certificate_bundles_from_query):
        if certificate_bundle_action.certificate_quantity is not None:
            if (
                granular_certificate_bundle.bundle_quantity
                <= certificate_bundle_action.certificate_quantity
            ):
                certificates_bundles_to_transfer.append(
                    write_session.merge(granular_certificate_bundle)
                )
                continue

        child_bundle_1, _child_bundle_2 = split_certificate_bundle(
            granular_certificate_bundle,
            certificates_bundles_to_split[idx],
            write_session,
            read_session,
            esdb_client,
        )
        if child_bundle_1:
            certificates_bundles_to_transfer.append(write_session.merge(child_bundle_1))

    return certificates_bundles_to_transfer


def query_certificate_bundles(
    certificate_query: GranularCertificateQuery,
    read_session: Session | None = None,
    write_session: Session | None = None,
) -> list[GranularCertificateBundle] | None:
    """Query certificates based on the given filter parameters.

    By default will return read versions of the GC bundles, but if update operations
    are to be performed on them then passing a write session will override the
    read session and return instances from the writer database with the associated
    ActiveUtils methods.

    If no certificates are found with the given query parameters, will return None.

    Args:
        certificate_query (GranularCertificateAction): The certificate action
        read_session (Session): The database read session
        write_session (Session | None): The database write session

    Returns:
        list[GranularCertificateBundle]: The list of certificates

    """

    if (read_session is None) & (write_session is None):
        logger.error(
            "Either a read or a write session is required for querying certificates."
        )
        return None

    session: Session = read_session if write_session is None else write_session  # type: ignore

    # Query certificates based on the given filter parameters, without returning deleted
    # certificates
    stmt: SelectOfScalar = select(GranularCertificateBundle).where(
        GranularCertificateBundle.account_id == certificate_query.source_id,
        ~GranularCertificateBundle.is_deleted,
    )

    exclude = {"user_id", "localise_time", "source_id"}
    for query_param, query_value in certificate_query.model_dump(
        exclude=exclude
    ).items():
        if query_value is None:
            continue
        if query_param == "issuance_ids":
            device_interval_pairs = [
                issuance_id_to_device_and_interval(issuance_id)
                for issuance_id in query_value
            ]
            sparse_filter_clauses = [
                (
                    (GranularCertificateBundle.device_id == device_id)
                    & (
                        GranularCertificateBundle.production_starting_interval
                        == production_starting_interval
                    )
                )
                for (
                    device_id,
                    production_starting_interval,
                ) in device_interval_pairs
            ]
            stmt = select(GranularCertificateBundle).where(or_(*sparse_filter_clauses))
            break
        elif query_param == "certificate_period_start":
            stmt = stmt.where(
                GranularCertificateBundle.production_starting_interval >= query_value
            )
        elif query_param == "certificate_period_end":
            stmt = stmt.where(
                GranularCertificateBundle.production_ending_interval <= query_value
            )
        else:
            stmt = stmt.where(
                getattr(GranularCertificateBundle, query_param) == query_value
            )

    granular_certificate_bundles = session.exec(stmt).all()

    return granular_certificate_bundles


def get_certificate_bundles_by_account_id(
    account_id: int,
    read_session: Session,
    limit: int | None = None,
) -> list[GranularCertificateBundle] | None:
    certificate_bundle_query: SelectOfScalar = (
        select(GranularCertificateBundle)
        .filter(
            GranularCertificateBundle.account_id == account_id,
            ~GranularCertificateBundle.is_deleted,
        )
        .order_by(desc(GranularCertificateBundle.production_starting_interval))
    )

    if limit:
        certificate_bundle_query = certificate_bundle_query.limit(limit)

    certificate_bundles = read_session.exec(certificate_bundle_query).all()

    return list(certificate_bundles)


def transfer_certificates(
    certificate_bundle_action: GranularCertificateTransfer,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> ActionResult | None:
    """Transfer a fixed number of certificates matched to the given filter parameters to the specified target Account.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    if not Account.exists(certificate_bundle_action.target_id, write_session):
        err_msg = (
            f"Target account does not exist: {certificate_bundle_action.target_id}"
        )
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Check that the target account has whitelisted the source account
    account_whitelist = read_session.exec(
        select(AccountWhitelistLink.source_account_id).where(
            AccountWhitelistLink.target_account_id
            == certificate_bundle_action.target_id,
            ~AccountWhitelistLink.is_deleted,
        )
    ).all()
    if certificate_bundle_action.source_id not in account_whitelist:
        err_msg = f"Target account ({certificate_bundle_action.target_id}) has not whitelisted the source account ({certificate_bundle_action.source_id}) for transfer."
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Retrieve certificates to transfer
    certificate_bundles_from_query = get_certificate_bundles_by_id(
        certificate_bundle_action.granular_certificate_bundle_ids, write_session
    )

    if not certificate_bundles_from_query:
        err_msg = "No certificates found to transfer with given query parameters."
        logger.error(err_msg)
        raise ValueError(err_msg)

    if any(
        c.certificate_bundle_status != CertificateStatus.ACTIVE
        for c in certificate_bundles_from_query
    ):
        err_msg = f"Can only transfer active certificates, found: { {c.certificate_bundle_status for c in certificate_bundles_from_query} }"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_bundles_to_transfer = apply_bundle_quantity_or_percentage(
        certificate_bundles_from_query,
        certificate_bundle_action,
        write_session,
        read_session,
        esdb_client,
    )

    # Transfer certificates by updating account ID of target bundle
    for certificate in certificates_bundles_to_transfer:
        certificate_update = GranularCertificateBundleUpdate(
            account_id=certificate_bundle_action.target_id
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return ActionResult(
        action_type=CertificateActionType.TRANSFER,
        action_result=ActionOutcome.SUCCESS,
        details=f"Transferred {len(certificates_bundles_to_transfer)} certificates to account {certificate_bundle_action.target_id}.",
    )


def cancel_certificates(
    certificate_cancel: GranularCertificateCancel,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> ActionResult | None:
    """Cancel certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # Retrieve certificates to cancel
    certificate_bundles_from_query = get_certificate_bundles_by_id(
        certificate_cancel.granular_certificate_bundle_ids, write_session
    )

    if not certificate_bundles_from_query:
        err_msg = "No certificates found to cancel with given query parameters."
        logger.error(err_msg)
        raise ValueError(err_msg)

    valid_statuses = [CertificateStatus.ACTIVE, CertificateStatus.RESERVED]
    if any(
        c.certificate_bundle_status not in valid_statuses
        for c in certificate_bundles_from_query
    ):
        err_msg = f"Certificates must be in ACTIVE or RESERVED status to cancel, found: { {c.certificate_bundle_status for c in certificate_bundles_from_query} }"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_bundles_to_cancel = apply_bundle_quantity_or_percentage(
        certificate_bundles_from_query,
        certificate_cancel,
        write_session,
        read_session,
        esdb_client,
    )

    # Cancel certificates
    for certificate in certificates_bundles_to_cancel:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_bundle_status=CertificateStatus.CANCELLED,
            beneficiary=certificate_cancel.beneficiary,
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return ActionResult(
        action_type=CertificateActionType.CANCEL,
        action_result=ActionOutcome.SUCCESS,
        details=f"Cancelled {len(certificates_bundles_to_cancel)} certificates.",
    )


def cancel_certificates_for_storage(
    certificate_cancel: GranularCertificateCancelStorage,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> ActionResult | None:
    """Cancel certificates for storage matched to the given filter parameters.
    Args:
        certificate_cancel (GranularCertificateCancelStorage): The certificate cancel action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client
    """

    # Retrieve certificates to cancel
    certificate_bundles_from_query = get_certificate_bundles_by_id(
        certificate_cancel.granular_certificate_bundle_ids, write_session
    )

    if not certificate_bundles_from_query:
        err_msg = "No certificates found to cancel with given query parameters."
        logger.error(err_msg)
        raise ValueError(err_msg)

    valid_statuses = [CertificateStatus.ACTIVE, CertificateStatus.RESERVED]
    if any(
        c.certificate_bundle_status not in valid_statuses
        for c in certificate_bundles_from_query
    ):
        err_msg = f"Certificates must be in ACTIVE or RESERVED status to cancel, found: { {c.certificate_bundle_status for c in certificate_bundles_from_query} }"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # get the storage device by local device identifier
    storage_device = get_device_by_local_identifier(
        read_session, certificate_cancel.storage_local_device_identifier
    )

    if not storage_device:
        err_msg = f"Storage device with local identifier {certificate_cancel.storage_local_device_identifier} not found."
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_bundles_to_cancel = apply_bundle_quantity_or_percentage(
        certificate_bundles_from_query,
        certificate_cancel,
        write_session,
        read_session,
        esdb_client,
    )

    # Cancel certificates and issue SDGCs against allocated storage records where applicable
    allocated_storage_records: list[SQLModel] = []

    for certificate in certificates_bundles_to_cancel:
        beneficiary = (
            f"for storage: {certificate_cancel.storage_local_device_identifier}"
        )

        certificate_update = GranularCertificateBundleUpdate(
            certificate_bundle_status=CertificateStatus.CANCELLED_FOR_STORAGE,
            beneficiary=beneficiary,
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

        # 1. Check if storage records exist
        storage_record = get_storage_record_by_device_id_and_interval(
            read_session,
            certificate.device_id,
            certificate.production_starting_interval,
        )
        if storage_record is None or storage_record.id is None:
            # Cancel certificate and continue to next
            continue

        if not storage_record.is_charging:
            raise ValueError(
                f"Storage record for device {certificate.device_id} and interval {certificate.production_starting_interval} is not a charging."
            )

        allocated_storage_record = get_allocated_storage_records_for_storage_record_id(
            read_session, storage_record.id
        )
        if not allocated_storage_record:
            continue

        # Update storage record with the cancelled certificate
        for asr in allocated_storage_record:
            asr_update = AllocatedStorageRecordUpdate(gc_allocation_id=certificate.id)
            updated_asr = asr.update(
                asr_update,
                write_session,
                read_session,
                esdb_client,
            )
            if updated_asr:
                allocated_storage_records.append(updated_asr)

    if allocated_storage_records:
        issued_sdgcs = issue_sdgcs_against_allocated_records(
            allocated_storage_records=allocated_storage_records,  # type: ignore
            device=storage_device,
            account_id=storage_device.account_id,
            write_session=write_session,
            read_session=read_session,
            esdb_client=esdb_client,
        )

    return ActionResult(
        action_type=CertificateActionType.CANCEL_FOR_STORAGE,
        action_result=ActionOutcome.SUCCESS,
        details=f"Cancelled {len(certificates_bundles_to_cancel)} certificates for storage and issued {len(issued_sdgcs)} SDGCs.",
    )


def claim_certificates(
    certificate_claim: GranularCertificateClaim,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> ActionResult | None:
    """Claim certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # Retrieve certificates to claim
    certificate_bundles_from_query = get_certificate_bundles_by_id(
        certificate_claim.granular_certificate_bundle_ids, write_session
    )

    if not certificate_bundles_from_query:
        err_msg = "No certificates found to claim with given query parameters."
        logger.error(err_msg)
        raise ValueError(err_msg)

    if any(
        c.certificate_bundle_status != CertificateStatus.CANCELLED
        for c in certificate_bundles_from_query
    ):
        err_msg = f"Can only claim cancelled certificates, found: { {c.certificate_bundle_status for c in certificate_bundles_from_query} }"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_bundles_to_claim = apply_bundle_quantity_or_percentage(
        certificate_bundles_from_query,
        certificate_claim,
        write_session,
        read_session,
        esdb_client,
    )

    # Assert the certificates are in a cancelled state
    for certificate in certificates_bundles_to_claim:
        assert (
            certificate.certificate_bundle_status == CertificateStatus.CANCELLED
        ), f"Certificate with ID {certificate.issuance_id} is not cancelled and cannot be claimed"

        certificate_update = GranularCertificateBundleUpdate(
            certificate_bundle_status=CertificateStatus.CLAIMED
        )

        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return ActionResult(
        action_type=CertificateActionType.CLAIM,
        action_result=ActionOutcome.SUCCESS,
        details=f"Claimed {len(certificates_bundles_to_claim)} certificates.",
    )


def withdraw_certificates(
    certificate_bundle_action: GranularCertificateWithdraw,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> ActionResult | None:
    """Withdraw certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # TODO add logic for removing withdrawn GCs from the main table

    # Retrieve certificates to withdraw
    certificate_bundles_from_query = get_certificate_bundles_by_id(
        certificate_bundle_action.granular_certificate_bundle_ids, write_session
    )

    if not certificate_bundles_from_query:
        err_msg = "No certificates found to withdraw with given query parameters."
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_bundles_to_withdraw = apply_bundle_quantity_or_percentage(
        certificate_bundles_from_query,
        certificate_bundle_action,
        write_session,
        read_session,
        esdb_client,
    )

    # Withdraw certificates
    for certificate in certificates_bundles_to_withdraw:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_bundle_status=CertificateStatus.WITHDRAWN
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return ActionResult(
        action_type=CertificateActionType.WITHDRAW,
        action_result=ActionOutcome.SUCCESS,
        details=f"Withdrawn {len(certificates_bundles_to_withdraw)} certificates.",
    )


def lock_certificates(
    certificate_bundle_action: GranularCertificateLock,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> ActionResult | None:
    """Lock certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    Returns:
        list[GranularCertificateAction]: The list of certificates locked

    """

    # Retrieve certificates to lock
    certificate_bundles_from_query = get_certificate_bundles_by_id(
        certificate_bundle_action.granular_certificate_bundle_ids, write_session
    )

    if not certificate_bundles_from_query:
        err_msg = "No certificates found to lock with given query parameters."
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_bundles_to_lock = apply_bundle_quantity_or_percentage(
        certificate_bundles_from_query,
        certificate_bundle_action,
        write_session,
        read_session,
        esdb_client,
    )

    # Lock certificates
    for certificate in certificates_bundles_to_lock:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_bundle_status=CertificateStatus.LOCKED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return ActionResult(
        action_type=CertificateActionType.LOCK,
        action_result=ActionOutcome.SUCCESS,
        details=f"Locked {len(certificates_bundles_to_lock)} certificates.",
    )


def reserve_certificates(
    certificate_reserve: GranularCertificateReserve,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> ActionResult | None:
    """Reserve certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # Retrieve certificates to reserve
    certificate_bundles_from_query = get_certificate_bundles_by_id(
        certificate_reserve.granular_certificate_bundle_ids, write_session
    )

    if not certificate_bundles_from_query:
        err_msg = "No certificates found to reserve with given query parameters."
        logger.error(err_msg)
        raise ValueError(err_msg)

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_bundles_to_reserve = apply_bundle_quantity_or_percentage(
        certificate_bundles_from_query,
        certificate_reserve,
        write_session,
        read_session,
        esdb_client,
    )

    # Reserve certificates
    for certificate in certificates_bundles_to_reserve:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_bundle_status=CertificateStatus.RESERVED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return ActionResult(
        action_type=CertificateActionType.RESERVE,
        action_result=ActionOutcome.SUCCESS,
        details=f"Reserved {len(certificates_bundles_to_reserve)} certificates.",
    )


def get_latest_issuance_metadata(db_session: Session) -> IssuanceMetaData | None:
    """Get the latest IssuanceMetaData based on created_at.

    Args:
        db_session (Session): The database session
    Returns:
        int: The latest issuance metadata object

    """
    stmt: SelectOfScalar = (
        select(IssuanceMetaData).order_by(desc(IssuanceMetaData.created_at)).limit(1)
    )
    latest_issuance_metadata = db_session.exec(stmt).first()

    if not latest_issuance_metadata:
        return None
    else:
        return latest_issuance_metadata


def import_gc_bundles(
    account_id: int,
    gc_df: pd.DataFrame,
    device_json: str,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> list[GranularCertificateBundle]:
    """Import GC bundles from a CSV file.

    Args:
        account_id (int): The account ID to assign to the imported GCs
        gc_df (pd.DataFrame): DataFrame containing both IssuanceMetaData and GranularCertificateBundle attributes
        device_json (DeviceBase): Device details of the issuing device
        write_session (Session): Database write session
        read_session (Session): Database read session
        esdb_client (EventStoreDBClient): EventStoreDB client

    Returns:
        list[GranularCertificateBundle]: List of created GC bundles
    """
    device_dict = json.loads(device_json)
    if device_dict.get("device_name") is None:
        raise ValueError("Device name is required to import certificates.")

    # If the device is not present, all details must be provided
    import_device = create_import_device(
        device_dict, write_session, read_session, esdb_client
    )

    gc_df["device_id"] = import_device.id
    gc_df["account_id"] = account_id

    # Define the IssuanceMetaData fields
    issuance_metadata_fields = list(IssuanceMetaDataBase.model_fields.keys())

    # Create a mapping from unique IssuanceMetaData combinations to their IDs
    metadata_mapping = {}

    # Group by unique IssuanceMetaData combinations and create them
    unique_metadata_groups = gc_df[issuance_metadata_fields].drop_duplicates()

    for _, metadata_row in unique_metadata_groups.iterrows():
        metadata_dict = metadata_row.to_dict()

        metadata_records = IssuanceMetaData.create(
            metadata_dict,
            write_session,
            read_session,
            esdb_client,
        )

        if metadata_records is None:
            raise ValueError(f"Could not create IssuanceMetaData for: {metadata_dict}")

        metadata_record = cast(IssuanceMetaData, metadata_records[0])
        metadata_id = metadata_record.id

        # Create a hashable key for the metadata combination, replacing NaN values with None
        metadata_key = tuple(
            sorted((k, v if not pd.isna(v) else None) for k, v in metadata_dict.items())
        )
        metadata_mapping[metadata_key] = metadata_id

    # Now create the GC bundles with the correct metadata_id
    gc_bundles_data = []

    # Retrieve existing bundles for the import device once for validation
    if import_device.id is None:
        raise ValueError("Import device ID is None. Cannot retrieve existing bundles.")

    existing_bundles = get_certificate_bundles_by_device_id(
        read_session, int(import_device.id)
    )

    for _, row in gc_df.iterrows():
        # Create the metadata key for this row
        metadata_key = tuple(
            sorted(
                (k, v if not pd.isna(v) else None)
                for k, v in row[issuance_metadata_fields].to_dict().items()
            )
        )
        metadata_id = metadata_mapping[metadata_key]

        # Create the GC bundle data dict, excluding metadata fields and adding metadata_id
        bundle_data = row.drop(issuance_metadata_fields).to_dict()

        # Replace nan values with None
        bundle_data = {k: (None if pd.isna(v) else v) for k, v in bundle_data.items()}

        bundle_data["metadata_id"] = metadata_id
        bundle_data["hash"] = create_bundle_hash(bundle_data, None)
        bundle_data["certificate_bundle_status"] = CertificateStatus.ACTIVE
        bundle_data["production_starting_interval"] = pd.to_datetime(
            bundle_data["production_starting_interval"], utc=True
        ).strftime("%Y-%m-%d %H:%M:%S")
        bundle_data["production_ending_interval"] = pd.to_datetime(
            bundle_data["production_ending_interval"], utc=True
        ).strftime("%Y-%m-%d %H:%M:%S")
        bundle_data["expiry_datestamp"] = pd.to_datetime(
            bundle_data["expiry_datestamp"], utc=True
        ).strftime("%Y-%m-%d")

        # Validate the bundle range start and end IDs
        validate_imported_granular_certificate_bundle(
            bundle_data, existing_bundles, import_device
        )

        gc_bundles_data.append(bundle_data)

    # Create the GC bundles
    gc_bundles = GranularCertificateBundle.create(
        gc_bundles_data,
        write_session,
        read_session,
        esdb_client,
    )

    if gc_bundles is None:
        raise ValueError("Could not create GC bundles.")

    gc_bundles_cast = [
        cast(GranularCertificateBundle, gc_bundle) for gc_bundle in gc_bundles
    ]

    return gc_bundles_cast
