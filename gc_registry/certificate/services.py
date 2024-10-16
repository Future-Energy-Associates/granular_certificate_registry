import datetime
import logging
from hashlib import sha256

from esdbclient import EventStoreDBClient
from fluent_validator import validate  # type: ignore
from sqlalchemy import func
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import (
    CertificateStatus,
    GranularCertificateBundleBase,
    GranularCertificateBundleCreate,
)
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
    automcatically generated fields such as the bundle's ID.

    Args:
        gc_bundle (GranularCertificateBundle): The child GC Bundle
        nonce (str): The hash of the parent GC Bundle

    Returns:
        str: The hash of the child GC Bundle
    """

    return sha256(
        f"{gc_bundle.model_dump_json(exclude='id')}{nonce}".encode()
    ).hexdigest()


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
    gc_bundle_child_1 = GranularCertificateBundleBase(**gc_bundle.model_dump())
    gc_bundle_child_2 = GranularCertificateBundleBase(**gc_bundle.model_dump())

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

    # Validate the bundle face value is equal to the difference between the bundle ID range
    # and less than the device max watts hours
    validate(gcb.face_value, identifier="face_value").less_than(
        device_max_watts_hours
    ).equal(gcb.bundle_id_range_end - gcb.bundle_id_range_start)

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
