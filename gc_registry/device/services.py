import logging
from typing import Any, cast

from esdbclient import EventStoreDBClient
from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.account.models import Account
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.device.models import Device, DeviceCreate
from gc_registry.settings import settings

logger = logging.getLogger(__name__)


def get_all_devices(db_session: Session) -> list[Device]:
    stmt: SelectOfScalar = select(Device)
    devices = db_session.exec(stmt).all()

    return list(devices)


def get_devices_by_account_id(account_id: int, db_session: Session) -> list[Device]:
    stmt: SelectOfScalar = select(Device).where(Device.account_id == account_id)
    devices = db_session.exec(stmt).all()

    return list(devices)


def get_certificate_devices_by_account_id(
    db_session: Session, account_id: int
) -> list[Device]:
    stmt: SelectOfScalar = (
        select(Device)
        .join(GranularCertificateBundle)
        .where(
            GranularCertificateBundle.device_id == Device.id,
            GranularCertificateBundle.account_id == account_id,
        )
        .distinct()
    )
    devices = db_session.exec(stmt).all()

    return list(devices)


def get_device_capacity_by_id(db_session: Session, device_id: int) -> float | None:
    stmt: SelectOfScalar = select(Device.power_mw).where(Device.id == device_id)
    device_capacity = db_session.exec(stmt).first()
    if device_capacity:
        return float(device_capacity)
    else:
        return None


def get_device_by_id(db_session: Session, device_id: int) -> Device | None:
    stmt: SelectOfScalar = select(Device).where(Device.id == device_id)
    device = db_session.exec(stmt).first()
    return device


def get_device_by_local_identifier(
    db_session: Session, local_device_identifier: str
) -> Device | None:
    """Get a device by its local identifier."""
    query: SelectOfScalar = select(Device).where(
        Device.local_device_identifier == local_device_identifier,
        ~Device.is_deleted,
    )

    device = db_session.exec(query).first()
    return device


def device_mw_capacity_to_wh_max(
    device_capacity_mw: float, hours: float = settings.CERTIFICATE_GRANULARITY_HOURS
) -> float:
    """Take the device capacity in MW and calculate the maximum Watt-Hours
    the device can produce in a given number of hours"""
    W_IN_MW = 1e6
    return device_capacity_mw * W_IN_MW * hours


def map_device_to_certificate_read(device: Device) -> dict:
    mapped_columns = ["id", "technology_type", "power_mw", "location", "energy_mwh"]

    device_dict = device.model_dump().copy()
    device_dict_original = device_dict.copy()

    device_dict = {f"device_{k}": device_dict[k] for k in mapped_columns}

    not_mapped_columns = [
        k for k in device_dict_original.keys() if k not in mapped_columns
    ]
    for k in not_mapped_columns:
        device_dict[k] = device_dict_original[k]

    device_dict["device_production_start_date"] = device_dict_original[
        "operational_date"
    ]

    return device_dict


def get_certificate_bundles_by_device_id(
    db_session: Session, device_id: int
) -> list[GranularCertificateBundle]:
    stmt: SelectOfScalar = select(GranularCertificateBundle).where(
        GranularCertificateBundle.device_id == device_id
    )
    certificate_bundles = db_session.exec(stmt).all()
    return list(certificate_bundles)


def create_import_device(
    device_dict: dict[str, Any],
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> Device:
    """Create an import device for a certificate import.

    To maintain certificate validation services within the registry, each unique import device
    is replicated within GCOS and assigned to an 'Import Account' that is not associated with any
    user or organisation. The import device is used to track the import of certificates from another registry
    and validate the certificates against the import device's characteristics and previous GC imports.

    Args:
        device_dict (dict[str, Any]): The device dictionary.
        write_session (Session): The database write session.
        read_session (Session): The read session.
        esdb_client (EventStoreDBClient): The event store DB client.

    Returns:
        Device: The created device.
    """
    # Check whether the device already exists
    import_device = Device.by_name(device_dict["device_name"], read_session)
    if import_device is not None:
        return import_device

    logger.info(f"Creating import device: {device_dict}...")
    if "account_id" in device_dict:
        import_account_id = device_dict["account_id"]
    else:
        import_account = Account.by_name("Import Account", read_session)
        if import_account is None:
            raise ValueError("Import account not found.")
        import_account_id = import_account.id
        device_dict["account_id"] = import_account_id

    device_create = DeviceCreate.model_validate(device_dict)
    device = Device.create(device_create, write_session, read_session, esdb_client)
    if device is None:
        raise ValueError("Could not create import device.")

    logger.info("Created import device.")

    return cast(Device, device[0])
