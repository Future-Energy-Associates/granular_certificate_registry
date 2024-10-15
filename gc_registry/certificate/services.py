import datetime
import logging

from esdbclient import EventStoreDBClient
from fluent_validator import validate
from sqlalchemy import func, select
from sqlmodel import Session

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import (
    CertificateStatus,
    GranularCertificateBundleBase,
)
from gc_registry.device.meter_data.abstract_client import MeterDataClient
from gc_registry.device.services import (
    device_mw_capacity_to_wh_max,
    get_all_devices,
    get_device_capacity_by_id,
)
from gc_registry.settings import settings


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

    stmt = select(func.max(GranularCertificateBundle.bundle_id_range_end)).where(
        GranularCertificateBundle.device_id == device_id,
        GranularCertificateBundle.certificate_status != CertificateStatus.WITHDRAWN,
    )

    max_certificate_id = db_session.exec(stmt).first()

    if not max_certificate_id[0]:
        return None
    else:
        return int(max_certificate_id[0])


def validate_granular_certificate_bundle(
    db_session: Session,
    gcb: GranularCertificateBundleBase,
    is_storage_device: bool,
    hours: float = settings.CERTIFICATE_GRANULARITY_HOURS,
) -> None:
    W_IN_MW = 1e6
    device_id = gcb.device_id
    device_mw = get_device_capacity_by_id(db_session, device_id) / W_IN_MW
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
    meter_data_client: MeterDataClient,
) -> list[GranularCertificateBundle]:
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
    devices = [d[0] for d in get_all_devices(db_read_engine)]

    # Issue certificates for each device
    certificates = []
    for device in devices:
        # Get the meter data for the device
        if not device.meter_data_id:
            logging.error(f"No meter data ID for device: {device.id}")
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
