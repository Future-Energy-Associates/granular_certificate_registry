import datetime
import logging
from typing import Any

from esdbclient import EventStoreDBClient
from sqlalchemy import func
from sqlmodel import Session, SQLModel, select
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
    certificate_query_param_map,
)
from gc_registry.certificate.validation import validate_granular_certificate_bundle
from gc_registry.core.database import cqrs
from gc_registry.core.models.base import CertificateActionType
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.meter_data.abstract_meter_client import AbstractMeterDataClient
from gc_registry.device.models import Device
from gc_registry.device.services import get_all_devices


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

    # Mark the parent bundle as deleted
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
    if not device.id or not device.meter_data_id:
        logging.error(f"No device ID or meter data ID for device: {device}")
        return None

    meter_data = meter_data_client.get_metering_by_device_in_datetime_range(
        from_datetime, to_datetime, device.meter_data_id
    )

    if not meter_data:
        logging.info(f"No meter data retrieved for device: {device.meter_data_id}")
        return None

    # Map the meter data to certificates
    bundle_id_range_start = get_max_certificate_id_by_device_id(
        db_read_session, device.id
    )
    if not bundle_id_range_start:
        bundle_id_range_start = 1
    else:
        bundle_id_range_start += 1

    certificates = meter_data_client.map_metering_to_certificates(
        generation_data=meter_data,
        bundle_id_range_start=bundle_id_range_start,
        account_id=device.account_id,
        device_id=device.id,
        is_storage=device.is_storage,
        issuance_metadata_id=issuance_metadata_id,
    )

    if not certificates:
        logging.error(f"No meter data retrieved for device: {device.meter_data_id}")
        return None

    # Validate the certificates
    valid_certificates = []
    for certificate in certificates:
        device_max_certificate_id = get_max_certificate_id_by_device_id(
            db_read_session, device.id
        )

        valid_certificate = validate_granular_certificate_bundle(
            db_read_session,
            certificate,
            is_storage_device=device.is_storage,
            device_max_certificate_id=device_max_certificate_id,
        )
        valid_certificate.hash = create_bundle_hash(valid_certificate, nonce="")
        valid_certificate.issuance_id = create_issuance_id(valid_certificate)
        valid_certificates.append(valid_certificate)

    # Commit the certificate to the database
    # TODO: Consider using bulk transaction - will require change in validation of bundle_id_range_start and end
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
        logging.error("No devices found in the registry")
        return None

    # Issue certificates for each device
    certificates: list[Any] = []
    for device in devices:
        # Get the meter data for the device
        if not device.meter_data_id:
            logging.error(f"No meter data ID for device: {device.id}")
            continue

        if not device.id:
            logging.error(f"No device ID for device: {device}")
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
    certificate_action.action_request_datetime = datetime.datetime.now(
        tz=datetime.timezone.utc
    )
    certificate_action.action_complete_datetime_local = datetime.datetime.now()

    certificate_action_functions = {
        CertificateActionType.TRANSFER: transfer_certificates,
        CertificateActionType.CANCEL: cancel_certificates,
        CertificateActionType.CLAIM: claim_certificates,
        CertificateActionType.WITHDRAW: withdraw_certificates,
        CertificateActionType.LOCK: lock_certificates,
        CertificateActionType.RESERVE: reserve_certificates,
    }

    assert (
        certificate_action.action_type in certificate_action_functions
    ), "Invalid action type."  # type: ignore

    try:
        certificate_action_functions[certificate_action.action_type](  # type: ignore
            certificate_action, write_session, read_session, esdb_client
        )
    except Exception as e:
        logging.error(f"Error whilst processing certificate action: {str(e)}")
        certificate_action.action_response_status = "rejected"
    else:
        certificate_action.action_response_status = "accepted"

    db_certificate_action = GranularCertificateAction.create(
        certificate_action, write_session, read_session, esdb_client
    )
    if not db_certificate_action:
        logging.error("Error creating certificate action entity")
        return None

    return db_certificate_action[0]  # type: ignore


def query_certificates(
    certificate_query: GranularCertificateActionBase, db_read_engine: Session
) -> list[GranularCertificateBundle] | None:
    """Query certificates based on the given filter parameters.

    Args:
        certificate_query (GranularCertificateAction): The certificate action
        db_read_engine (Session): The database read session

    Returns:
        list[GranularCertificateAction]: The list of certificates

    """

    # Query certificates based on the given filter parameters
    stmt = select(GranularCertificateBundle)  # type: ignore
    for query_param, query_value in certificate_query.model_dump().items():
        if (query_param in certificate_query_param_map) & (query_value is not None):
            if query_param == "certificate_period_start":
                stmt = stmt.where(
                    getattr(
                        GranularCertificateBundle,
                        certificate_query_param_map[query_param],  # type: ignore
                    )
                    >= query_value
                )
            elif query_param == "certificate_period_end":
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

    certificates = db_read_engine.exec(stmt).all()

    return certificates


def transfer_certificates(
    certificate_bundle_action: GranularCertificateActionBase,
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
    ), "Target account does not exist"

    # Retrieve certificates to transfer
    certificates_from_query = query_certificates(
        certificate_bundle_action, read_session
    )

    if not certificates_from_query:
        logging.error("No certificates found to transfer with given query parameters.")
        return None

    for certificate in certificates_from_query:
        assert (
            certificate.certificate_status == CertificateStatus.ACTIVE
        ), f"Certificate with ID {certificate.issuance_id} is not active and cannot be transferred"

    # Split bundles if required, but only if certificate_quantity is supplied
    certificates_to_transfer = []
    if certificate_bundle_action.certificate_quantity is not None:
        for certificate in certificates_from_query:
            certificate = write_session.merge(certificate)
            if (
                certificate.bundle_quantity
                > certificate_bundle_action.certificate_quantity
            ):
                chlid_bundle_1, _child_bundle_2 = split_certificate_bundle(
                    certificate,
                    certificate_bundle_action.certificate_quantity,
                    write_session,
                    read_session,
                    esdb_client,
                )
                if chlid_bundle_1:
                    certificates_to_transfer.append(chlid_bundle_1)
            else:
                certificates_to_transfer.append(certificate)
    else:
        certificates_to_transfer = certificates_from_query

    # Transfer certificates by updating account ID of target bundle
    for certificate in certificates_to_transfer:
        certificate_update = GranularCertificateBundleUpdate(
            account_id=certificate_bundle_action.target_id
        )
        certificate = write_session.merge(certificate)
        certificate.update(certificate_update, write_session, read_session, esdb_client)  # type: ignore

    return


def cancel_certificates(
    certificate_bundle_action: GranularCertificateActionBase,
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
    certificates_to_cancel = query_certificates(certificate_bundle_action, read_session)

    if not certificates_to_cancel:
        logging.info("No certificates found to cancel with given query parameters.")
        return

    # Cancel certificates
    for certificate in certificates_to_cancel:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.CANCELLED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def claim_certificates(
    certificate_bundle_action: GranularCertificateActionBase,
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

    # Claims need a beneficiary
    assert (
        certificate_bundle_action.beneficiary
    ), "Beneficiary ID is required for GC claims"

    # Retrieve certificates to claim
    certificates_to_claim = query_certificates(certificate_bundle_action, read_session)

    if not certificates_to_claim:
        logging.info("No certificates found to claim with given query parameters.")
        return

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
    certificate_bundle_action: GranularCertificateActionBase,
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
    certificates_to_withdraw = query_certificates(
        certificate_bundle_action, read_session
    )

    if not certificates_to_withdraw:
        logging.info("No certificates found to withdraw with given query parameters.")
        return

    # Withdraw certificates
    for certificate in certificates_to_withdraw:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.WITHDRAWN
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def lock_certificates(
    certificate_bundle_action: GranularCertificateActionBase,
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
    certificates_to_lock = query_certificates(certificate_bundle_action, read_session)

    if not certificates_to_lock:
        logging.info("No certificates found to lock with given query parameters.")
        return

    # Lock certificates
    for certificate in certificates_to_lock:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.LOCKED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def reserve_certificates(
    certificate_bundle_action: GranularCertificateActionBase,
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
    certificates_to_reserve = query_certificates(
        certificate_bundle_action, read_session
    )

    if not certificates_to_reserve:
        logging.info("No certificates found to reserve with given query parameters.")
        return

    # Reserve certificates
    for certificate in certificates_to_reserve:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.RESERVED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return
