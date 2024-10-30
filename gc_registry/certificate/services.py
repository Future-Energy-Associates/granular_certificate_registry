import datetime
import logging
from hashlib import sha256

from esdbclient import EventStoreDBClient
from fluent_validator import validate  # type: ignore
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
    mutable_gc_attributes,
)
from gc_registry.core.models.base import CertificateActionType
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.services import (
    device_mw_capacity_to_wh_max,
    get_all_devices,
    get_device_capacity_by_id,
)
from gc_registry.settings import settings


def create_bundle_hash(
    gc_bundle: GranularCertificateBundle | GranularCertificateBundleCreate,
    nonce: str = "",
):
    """
    Given a GC Bundle and a nonce taken from the hash of a parent bundle,
    return a new hash for the child bundle that demonstrates the child's
    lineage from the parent.

    To ensure that a consistent string representation of the GC bundle is
    used, a JSON model dump of the base bundle class is used to avoid
    automcatically generated fields such as the bundle's ID. In addition,
    only non-mutable fields are included such that lineage can be traced
    no matter the lifecycle stage the GC is in.

    Args:
        gc_bundle (GranularCertificateBundle): The child GC Bundle
        nonce (str): The hash of the parent GC Bundle

    Returns:
        str: The hash of the child GC Bundle
    """

    gc_bundle_dict = gc_bundle.model_dump_json(
        exclude=set(["id", "created_at", "hash"] + mutable_gc_attributes)
    )
    return sha256(f"{gc_bundle_dict}{nonce}".encode()).hexdigest()


def verifiy_bundle_lineage(
    gc_bundle_parent: GranularCertificateBundle,
    gc_bundle_child: GranularCertificateBundle,
):
    """
    Given a parent and child GC Bundle, verify that the child's hash
    can be recreated from the parent's hash and the child's nonce.

    Args:
        gc_bundle_parent (GranularCertificateBundle): The parent GC Bundle
        gc_bundle_child (GranularCertificateBundle): The child GC Bundle

    Returns:
        bool: Whether the child's hash can be recreated from the parent's hash
    """

    return (
        create_bundle_hash(gc_bundle_child, gc_bundle_parent.hash)
        == gc_bundle_child.hash
    )


def split_certificate_bundle(
    gc_bundle: GranularCertificateBundle,
    size_to_split: int,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
):
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
    gc_bundle.delete(write_session, read_session, esdb_client)

    # Write the child bundles to the database
    db_gc_bundle_child_1 = GranularCertificateBundle.create(
        gc_bundle_child_1, write_session, read_session, esdb_client
    )[0]
    db_gc_bundle_child_2 = GranularCertificateBundle.create(
        gc_bundle_child_2, write_session, read_session, esdb_client
    )[0]

    return db_gc_bundle_child_1, db_gc_bundle_child_2


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


def validate_granular_certificate_bundle(
    db_session: Session,
    gcb: GranularCertificateBundleBase,
    is_storage_device: bool,
    hours: float = settings.CERTIFICATE_GRANULARITY_HOURS,
) -> None:
    W_IN_MW = 1e6
    device_id = gcb.device_id
    device_w = get_device_capacity_by_id(db_session, device_id)
    if not device_w:
        raise ValueError(f"Device with ID {device_id} not found")

    device_mw = device_w / W_IN_MW
    device_max_watts_hours = device_mw_capacity_to_wh_max(device_mw, hours)

    device_max_certificate_id = get_max_certificate_id_by_device_id(
        db_session, device_id
    )

    if not device_max_certificate_id:
        device_max_certificate_id = 0

    # Validate the bundle quantity is equal to the difference between the bundle ID range
    # and less than the device max watts hours
    validate(gcb.bundle_quantity, identifier="bundle_quantity").less_than(
        device_max_watts_hours
    ).equal(gcb.bundle_id_range_end - gcb.bundle_id_range_start + 1)

    # Validate the bundle ID range start is greater than the previous max certificate ID
    validate(gcb.bundle_id_range_start, identifier="bundle_id_range_start").equal(
        device_max_certificate_id + 1
    )

    # At this point if integrating wtih EAC registry or possibility of cross registry transfer
    # add integrations with external sources for further validation e.g. cancellation of underlying EACs

    if is_storage_device:
        # TODO: add additional storage validation
        pass

    return None


def issue_certificates_in_date_range(
    from_datetime: datetime.datetime,
    to_datetime: datetime.datetime,
    db_write_engine: Session,
    db_read_engine: Session,
    esdb_client: EventStoreDBClient,
    issuance_metadata_id: int,
    meter_data_client: ElexonClient,
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
        db_write_engine (Session): The database write session
        db_read_engine (Session): The database read session
        issuance_metadata_id (int): The issuance metadata ID
        meter_data_client (MeterDataClient, optional): The meter data client. Defaults to Depends(ElexonClient).

    Returns:
        list[GranularCertificateBundle]: The list of certificates issued

    """

    # Get the devices in the registry
    devices = get_all_devices(db_read_engine)

    if not devices:
        logging.error("No devices found in the registry")
        return None

    # Issue certificates for each device
    certificates: list = []
    for device in devices:
        # Get the meter data for the device
        if not device.meter_data_id:
            logging.error(f"No meter data ID for device: {device.id}")
            continue

        if not device.id:
            logging.error(f"No device ID for device: {device}")
            continue

        meter_data = meter_data_client.get_generation_by_device_in_datetime_range(
            from_datetime, to_datetime, device.meter_data_id
        )

        if not meter_data:
            logging.info(f"No meter data retrieved for device: {device.meter_data_id}")
            continue

        # Map the meter data to certificates
        bundle_id_range_start = get_max_certificate_id_by_device_id(
            db_read_engine, device.id
        )
        if not bundle_id_range_start:
            bundle_id_range_start = 1
        else:
            bundle_id_range_start += 1

        certificates = meter_data_client.map_generation_to_certificates(
            meter_data,
            bundle_id_range_start,
            device.account_id,
            device.id,
            device.is_storage,
            issuance_metadata_id,
        )

        if not certificates:
            logging.info(f"No meter data retrieved for device: {device.meter_data_id}")
            continue

        # Validate the certificates
        for certificate in certificates:
            validate_granular_certificate_bundle(
                db_read_engine, certificate, is_storage_device=device.is_storage
            )

            # Commit the certificate to the database
            # TODO: Consider using bulk transaction - will require change in validation of bundle_id_range_start and end
            created_entities = GranularCertificateBundle.create(
                certificate, db_write_engine, db_read_engine, esdb_client
            )

    return created_entities


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
    }

    assert (
        certificate_action.action_type in certificate_action_functions
    ), "Invalid action type."

    try:
        certificate_action_functions[certificate_action.action_type](
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
    return db_certificate_action[0]


def query_certificates(
    certificate_query: GranularCertificateActionBase, db_read_engine: Session
) -> list[GranularCertificateBundleRead] | None:
    """Query certificates based on the given filter parameters.

    Args:
        certificate_query (GranularCertificateAction): The certificate action
        db_read_engine (Session): The database read session

    Returns:
        list[GranularCertificateAction]: The list of certificates

    """

    # Query certificates based on the given filter parameters
    stmt = select(GranularCertificateBundle)
    for query_param, query_value in certificate_query.model_dump().items():
        if (query_param in certificate_query_param_map) & (query_value is not None):
            if query_param == "certificate_period_start":
                stmt = stmt.where(
                    getattr(
                        GranularCertificateBundle,
                        certificate_query_param_map[query_param],
                    )
                    >= query_value
                )
            elif query_param == "certificate_period_end":
                stmt = stmt.where(
                    getattr(
                        GranularCertificateBundle,
                        certificate_query_param_map[query_param],
                    )
                    <= query_value
                )
            else:
                stmt = stmt.where(
                    getattr(
                        GranularCertificateBundle,
                        certificate_query_param_map[query_param],
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
) -> list[SQLModel] | None:
    """Transfer a fixed number of certificates matched to the given filter parameters to the specified target Account.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    Returns:
        list[GranularCertificateAction]: The list of certificates transferred

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
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return


def cancel_certificates(
    certificate_bundle_action: GranularCertificateActionBase,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> list[SQLModel] | None:
    """Cancel certificates matched to the given filter parameters.

    Args:
        certificate_bundle_action (GranularCertificateAction): The certificate action
        write_session (Session): The database write session
        read_session (Session): The database read session
        esdb_client (EventStoreDBClient): The EventStoreDB client

    Returns:
        list[GranularCertificateAction]: The list of certificates cancelled

    """

    # Retrieve certificates to cancel
    certificates_to_cancel = query_certificates(certificate_bundle_action, read_session)

    # Cancel certificates
    for certificate in certificates_to_cancel:
        certificate_update = GranularCertificateBundleUpdate(
            certificate_status=CertificateStatus.CANCELLED
        )
        certificate.update(certificate_update, write_session, read_session, esdb_client)

    return
