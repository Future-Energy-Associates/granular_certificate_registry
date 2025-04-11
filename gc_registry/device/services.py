from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.device.models import Device
from gc_registry.settings import settings


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
        .where(GranularCertificateBundle.account_id == account_id)
        .distinct()
    )
    devices = db_session.exec(stmt).all()

    return list(devices)


def get_device_capacity_by_id(db_session: Session, device_id: int) -> float | None:
    stmt: SelectOfScalar = select(Device.capacity).where(Device.id == device_id)
    device_capacity = db_session.exec(stmt).first()
    if device_capacity:
        return float(device_capacity)
    else:
        return None


def device_mw_capacity_to_wh_max(
    device_capacity_mw: float, hours: float = settings.CERTIFICATE_GRANULARITY_HOURS
) -> float:
    """Take the device capacity in MW and calculate the maximum Watt-Hours
    the device can produce in a given number of hours"""
    W_IN_MW = 1e6
    return device_capacity_mw * W_IN_MW * hours


def map_device_to_certificate_read(device: Device) -> dict:
    mapped_columns = ["id", "technology_type", "capacity", "location"]

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
