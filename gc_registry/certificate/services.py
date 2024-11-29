import datetime
from typing import Any, Callable

from esdbclient import EventStoreDBClient
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, SQLModel, or_, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.account.models import Account
from gc_registry.certificate.models import (
    GranularCertificateAction,
    GranularCertificateBundle,
    GranularCertificateBundleUpdate,
)
from gc_registry.certificate.schemas import (
    CertificateStatus,
    GranularCertificateActionBase,
    GranularCertificateBundleBase,
    GranularCertificateBundleCreate,
    GranularCertificateBundleRead,
    GranularCertificateCancel,
    GranularCertificateClaim,
    GranularCertificateLock,
    GranularCertificateQuery,
    GranularCertificateReserve,
    GranularCertificateTransfer,
    GranularCertificateWithdraw,
    certificate_query_param_map,
)
from gc_registry.certificate.validation import validate_granular_certificate_bundle
from gc_registry.core.database import cqrs
from gc_registry.core.models.base import CertificateActionType
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.meter_data.abstract_meter_client import AbstractMeterDataClient
from gc_registry.device.models import Device
from gc_registry.device.services import get_all_devices
from gc_registry.logging_config import logger


def get_certificate_bundles_by_id(
    gcb_ids: list[int], db_session: Session
) -> list[GranularCertificateBundle]:
    """Get a list of GC Bundles by their IDs.

    Args:
        gcb_ids (list[int]): The list of GC Bundle IDs
        db_session (Session): The database session

    Returns:
        list[GranularCertificateBundle]: The list of GC Bundles
    """

    stmt: SelectOfScalar = select(GranularCertificateBundle).where(
        GranularCertificateBundle.id.in_(gcb_ids)  # type: ignore
    )
    gc_bundles = db_session.exec(stmt).all()

    return gc_bundles


def split_certificate_bundle(
    gc_bundle: GranularCertificateBundle | GranularCertificateBundleRead,
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
        gc_bundle (GranularCertificateBundle): The parent GC Bundle
        size_to_split (int): The number of certificates to split from
            the parent bundle.

    Returns:
        tuple[GranularCertificateBundle, GranularCertificateBundle]: The two child GC Bundles
    """

    assert size_to_split > 0, "The size to split must be greater than 0"
    assert (
        size_to_split < gc_bundle.bundle_quantity
    ), "The size to split must be less than the total certificates in the parent bundle"

    # Create two child bundles
    gc_bundle_child_1 = GranularCertificateBundleCreate(**gc_bundle.model_dump())
    gc_bundle_child_2 = GranularCertificateBundleCreate(**gc_bundle.model_dump())

    # Update the child bundles with the new quantities
    gc_bundle_child_1.bundle_quantity = size_to_split
    gc_bundle_child_1.bundle_id_range_end = (
        gc_bundle_child_1.bundle_id_range_start + size_to_split
    )
    gc_bundle_child_1.hash = create_bundle_hash(gc_bundle_child_1, gc_bundle.hash)

    gc_bundle_child_2.bundle_quantity = gc_bundle.bundle_quantity - size_to_split
    gc_bundle_child_2.bundle_id_range_start = gc_bundle_child_1.bundle_id_range_end + 1
    gc_bundle_child_2.hash = create_bundle_hash(gc_bundle_child_2, gc_bundle.hash)

    # Mark the parent bundle as withdrawn and apply soft delete
    gc_bundle.certificate_status = CertificateStatus.BUNDLE_SPLIT
    gc_bundle.delete(write_session, read_session, esdb_client)  # type: ignore

    # Write the child bundles to the database
    db_gc_bundle_child_1 = GranularCertificateBundle.create(
        gc_bundle_child_1, write_session, read_session, esdb_client
    )
    db_gc_bundle_child_2 = GranularCertificateBundle.create(
        gc_bundle_child_2, write_session, read_session, esdb_client
    )

    return db_gc_bundle_child_1[0], db_gc_bundle_child_2[0]  # type: ignore


def create_issuance_id(gcb: GranularCertificateBundleBase) -> str:
    return f"{gcb.device_id}-{gcb.production_starting_interval}"


def issuance_id_to_device_and_interval(
    issuance_id: str,
) -> tuple[int, datetime.datetime]:
    parts = issuance_id.split("-")
    device_id = int(parts[0])
    interval = datetime.datetime.fromisoformat("-".join(parts[1:]))
    return device_id, interval


def get_max_certificate_id_by_device_id(
    db_session: Session, device_id: int
) -> int | None:
    """Gets the maximum certificate ID from any bundle for a given device, excluding any withdrawn certificates

    Args:
        db_session (Session): The database session
        device_id (int): The device ID

    Returns:
        int: The maximum certificate ID


    """

    stmt: SelectOfScalar = select(
        func.max(GranularCertificateBundle.bundle_id_range_end)
    ).where(
        GranularCertificateBundle.device_id == device_id,
        GranularCertificateBundle.certificate_status != CertificateStatus.WITHDRAWN,
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
        GranularCertificateBundle.certificate_status != CertificateStatus.WITHDRAWN,
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
    db_write_session: Session,
    db_read_session: Session,
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
        db_write_session (Session): The database write session
        db_read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client
        issuance_metadata_id (int): The issuance metadata ID
        meter_data_client (MeterDataClient, optional): The meter data client.

    Returns:
        list[GranularCertificateBundle]: The list of certificates issued
    """

    if not device.id or not device.meter_data_id:
        logger.error(f"No device ID or meter data ID for device: {device}")
        return None

    # get max timestamp already issued for the device
    max_issued_timestamp = get_max_certificate_timestamp_by_device_id(
        db_read_session, device.id
    )

    # check if the device has already been issued certificates for the given period
    if max_issued_timestamp and max_issued_timestamp >= to_datetime:
        logger.info(
            f"Device {device.id} has already been issued certificates for the period {from_datetime} to {to_datetime}"
        )
        return None

    # If max timestamp ias after from them use the max timestamp as the from_datetime
    if max_issued_timestamp and max_issued_timestamp > from_datetime:
        from_datetime = max_issued_timestamp

    # TODO CAG - this is messy by me, will refactor down the road
    # Also, validation later on assumes the metering data is datetime sorted -
    # can we guarantee this at the meter client level?
    if meter_data_client.NAME == "ManualSubmissionMeterClient":
        meter_data = meter_data_client.get_metering_by_device_in_datetime_range(
            from_datetime, to_datetime, device.id, db_read_session
        )
    else:
        meter_data = meter_data_client.get_metering_by_device_in_datetime_range(
            from_datetime, to_datetime, device.meter_data_id
        )

    if not meter_data:
        logger.info(f"No meter data retrieved for device: {device.meter_data_id}")
        return None

    # Map the meter data to certificates
    device_max_certificate_id = get_max_certificate_id_by_device_id(
        db_read_session, device.id
    )
    if not device_max_certificate_id:
        bundle_id_range_start = 1
    else:
        bundle_id_range_start = device_max_certificate_id + 1

    certificates = meter_data_client.map_metering_to_certificates(
        generation_data=meter_data,
        bundle_id_range_start=bundle_id_range_start,
        account_id=device.account_id,
        device=device,
        is_storage=device.is_storage,
        issuance_metadata_id=issuance_metadata_id,
    )

    if not certificates:
        logger.error(f"No meter data retrieved for device: {device.meter_data_id}")
        return None

    if not device_max_certificate_id:
        device_max_certificate_id = 0

    # Validate the certificates
    valid_certificates: list[Any] = []
    for certificate in certificates:
        # get max valid certificate max bundle id
        if valid_certificates:
            device_max_certificate_id = max(
                [v.bundle_id_range_end for v in valid_certificates]
            )

        if device_max_certificate_id is None:
            raise ValueError("Max certificate ID is None")

        valid_certificate = validate_granular_certificate_bundle(
            db_read_session,
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
        device_max_certificate_id = valid_certificate.bundle_id_range_end

    # Batch commit the GC bundles to the database
    created_entities = cqrs.write_to_database(
        valid_certificates,  # type: ignore
        db_write_session,
        db_read_session,
        esdb_client,
    )

    return created_entities


def issue_certificates_in_date_range(
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    db_write_session: Session,
    db_read_session: Session,
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
        db_write_session (Session): The database write session
        db_read_session (Session): The database read session
        issuance_metadata_id (int): The issuance metadata ID
        meter_data_client (MeterDataClient, optional): The meter data client. Defaults to Depends(ElexonClient).

    Returns:
        list[GranularCertificateBundle]: The list of certificates issued

    """

    # Get the devices in the registry
    devices = get_all_devices(db_read_session)

    if not devices:
        logger.error("No devices found in the registry")
        return None

    # Issue certificates for each device
    certificates: list[Any] = []
    for device in devices:
        logger.info(f"Issuing certificates for device: {device.id}")

        # Get the meter data for the device
        if not device.meter_data_id:
            logger.error(f"No meter data ID for device: {device.id}")
            continue

        if not device.id:
            logger.error(f"No device ID for device: {device}")
            continue

        created_entities = issue_certificates_by_device_in_date_range(
            device,
            from_datetime,
            to_datetime,
            db_write_session,
            db_read_session,
            esdb_client,
            issuance_metadata_id,
            meter_data_client,
        )
        if created_entities:
            certificates.extend(created_entities)

    return certificates


def process_certificate_action(
    certificate_action: GranularCertificateActionBase,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> GranularCertificateAction | None:
    """Process the given certificate action.

    Args:
        certificate_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    Returns:
        list[GranularCertificateAction]: The list of certificates processed

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
    }

    if valid_certificate_action.action_type not in certificate_action_functions.keys():
        raise ValueError(
            f"Action type ({valid_certificate_action.action_type}) not in {certificate_action_functions.keys()}"
        )

    # try:
    action_function: Callable[..., Any] = certificate_action_functions[
        valid_certificate_action.action_type
    ]
    action_function(certificate_action, write_session, read_session, esdb_client)
    # except Exception as e:
    #     logger.error(f"Error whilst processing certificate action: {str(e)}")

    db_certificate_actions = GranularCertificateAction.create(
        valid_certificate_action, write_session, read_session, esdb_client
    )

    return db_certificate_actions[0]  # type: ignore


def apply_bundle_quantity_or_percentage(
    certificates_from_query: list[GranularCertificateBundle],
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
        certificates_from_query (list[GranularCertificateBundle]): The certificates from the query
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
        return certificates_from_query

    certificates_to_transfer = []

    if certificate_bundle_action.certificate_quantity is not None:
        certificates_to_split = [
            certificate_bundle_action.certificate_quantity
            for i in range(len(certificates_from_query))
        ]
    elif certificate_bundle_action.certificate_bundle_percentage is not None:
        certificates_to_split = [
            int(
                certificate_bundle_action.certificate_bundle_percentage
                * certificate_from_query.bundle_quantity
            )
            for certificate_from_query in certificates_from_query
        ]

    # Only check the bundle quantity if the query on bundle quantity parameter is provided,
    # otherwise, split the bundle based on the percentage of the total certificates in the bundle
    for idx, gc_bundle in enumerate(certificates_from_query):
        if certificate_bundle_action.certificate_quantity is not None:
            if (
                gc_bundle.bundle_quantity
                <= certificate_bundle_action.certificate_quantity
            ):
                certificates_to_transfer.append(gc_bundle)
                continue

        child_bundle_1, _child_bundle_2 = split_certificate_bundle(
            gc_bundle,
            certificates_to_split[idx],
            write_session,
            read_session,
            esdb_client,
        )
        if child_bundle_1:
            certificates_to_transfer.append(child_bundle_1)

    return certificates_to_transfer


def query_certificates(
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
        db_read_engine (Session): The database read session
        db_write_engine (Session | None): The database write session

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
        GranularCertificateBundle.is_deleted == False,  # noqa
    )  # type: ignore

    for query_param, query_value in certificate_query.model_dump().items():
        if (query_param in certificate_query_param_map) & (query_value is not None):
            # sparse_filter_list overrides all other search criteria if provided
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
                stmt = select(GranularCertificateBundle).where(
                    or_(*sparse_filter_clauses)
                )
                break
            elif query_param in (
                "certificate_period_start",
                "source_certificate_bundle_id_range_start",
            ):
                stmt = stmt.where(
                    getattr(
                        GranularCertificateBundle,
                        certificate_query_param_map[query_param],  # type: ignore
                    )
                    >= query_value
                )
            elif query_param in (
                "certificate_period_end",
                "source_certificate_bundle_id_range_end",
            ):
                stmt = stmt.where(
                    getattr(
                        GranularCertificateBundle,
                        certificate_query_param_map[query_param],  # type: ignore
                    )
                    <= query_value
                )
            else:
                stmt = stmt.where(
                    getattr(
                        GranularCertificateBundle,
                        certificate_query_param_map[query_param],  # type: ignore
                    )
                    == query_value
                )

    gc_bundles = session.exec(stmt).all()

    return gc_bundles


def transfer_certificates(
    certificate_bundle_action: GranularCertificateTransfer,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> None:
    """Transfer a fixed number of certificates matched to the given filter parameters to the specified target Account.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    assert certificate_bundle_action.target_id, "Target account ID is required"
    assert Account.exists(
        certificate_bundle_action.target_id, write_session
    ), f"Target account does not exist: {certificate_bundle_action.target_id}"

    # Assert that the target account has whitelisted the source account
    account = Account.by_id(certificate_bundle_action.target_id, read_session)
    account_whitelist = (
        [] if account.account_whitelist is None else account.account_whitelist
    )
    if certificate_bundle_action.source_id not in account_whitelist:
        msg = f"""Target account ({certificate_bundle_action.target_id})
                  has not whitelisted the source account ({certificate_bundle_action.source_id})
                  for transfer."""
        raise HTTPException(status_code=403, detail=msg)

    # Retrieve certificates to transfer
    certificates_from_query = get_certificate_bundles_by_id(
        certificate_bundle_action.granular_certificate_bundle_ids, write_session
    )

    if not certificates_from_query:
        logger.error("No certificates found to transfer with given query parameters.")
        return None

    for certificate in certificates_from_query:
        assert (
            certificate.certificate_status == CertificateStatus.ACTIVE
        ), f"Certificate with ID {certificate.issuance_id} is not active and cannot be transferred"

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_to_transfer = apply_bundle_quantity_or_percentage(
        certificates_from_query,
        certificate_bundle_action,
        write_session,
        read_session,
        esdb_client,
    )

    # Transfer certificates by updating account ID of target bundle
    for certificate in certificates_to_transfer:
        certificate_update = GranularCertificateBundleUpdate(
            account_id=certificate_bundle_action.target_id
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)  # type: ignore

    return


def cancel_certificates(
    certificate_transfer: GranularCertificateCancel,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> None:
    """Cancel certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # Retrieve certificates to cancel
    certificates_from_query = get_certificate_bundles_by_id(
        certificate_transfer.granular_certificate_bundle_ids, write_session
    )

    if not certificates_from_query:
        logger.info("No certificates found to cancel with given query parameters.")
        return

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_to_cancel = apply_bundle_quantity_or_percentage(
        certificates_from_query,
        certificate_transfer,
        write_session,
        read_session,
        esdb_client,
    )

    # Cancel certificates
    for certificate in certificates_to_cancel:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.CANCELLED,
            beneficiary=certificate_transfer.beneficiary,
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def claim_certificates(
    certificate_claim: GranularCertificateClaim,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> None:
    """Claim certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # Retrieve certificates to claim
    certificates_from_query = get_certificate_bundles_by_id(
        certificate_claim.granular_certificate_bundle_ids, write_session
    )

    if not certificates_from_query:
        logger.info("No certificates found to claim with given query parameters.")
        return

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_to_claim = apply_bundle_quantity_or_percentage(
        certificates_from_query,
        certificate_claim,
        write_session,
        read_session,
        esdb_client,
    )

    # Assert the certificates are in a cancelled state
    for certificate in certificates_to_claim:
        assert (
            certificate.certificate_status == CertificateStatus.CANCELLED
        ), f"Certificate with ID {certificate.issuance_id} is not cancelled and cannot be claimed"

        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.CLAIMED
        )

        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def withdraw_certificates(
    certificate_bundle_action: GranularCertificateWithdraw,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> None:
    """Withdraw certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # TODO add logic for removing withdrawn GCs from the main table

    # Retrieve certificates to withdraw
    certificates_from_query = get_certificate_bundles_by_id(
        certificate_bundle_action.granular_certificate_bundle_ids, write_session
    )

    if not certificates_from_query:
        logger.info("No certificates found to withdraw with given query parameters.")
        return

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_to_withdraw = apply_bundle_quantity_or_percentage(
        certificates_from_query,
        certificate_bundle_action,
        write_session,
        read_session,
        esdb_client,
    )

    # Withdraw certificates
    for certificate in certificates_to_withdraw:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.WITHDRAWN
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def lock_certificates(
    certificate_bundle_action: GranularCertificateLock,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> None:
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
    certificates_from_query = get_certificate_bundles_by_id(
        certificate_bundle_action.granular_certificate_bundle_ids, write_session
    )

    if not certificates_from_query:
        logger.info("No certificates found to lock with given query parameters.")
        return

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_to_lock = apply_bundle_quantity_or_percentage(
        certificates_from_query,
        certificate_bundle_action,
        write_session,
        read_session,
        esdb_client,
    )

    # Lock certificates
    for certificate in certificates_to_lock:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.LOCKED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def reserve_certificates(
    certificate_reserve: GranularCertificateReserve,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> None:
    """Reserve certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    """

    # Retrieve certificates to reserve
    certificates_from_query = get_certificate_bundles_by_id(
        certificate_reserve.granular_certificate_bundle_ids, write_session
    )

    if not certificates_from_query:
        logger.info("No certificates found to reserve with given query parameters.")
        return

    # Split bundles if required, but only if certificate_quantity or percentage is provided
    certificates_to_reserve = apply_bundle_quantity_or_percentage(
        certificates_from_query,
        certificate_reserve,
        write_session,
        read_session,
        esdb_client,
    )

    # Reserve certificates
    for certificate in certificates_to_reserve:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.RESERVED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return
