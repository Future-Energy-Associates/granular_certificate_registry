from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.device.models import Device
from gc_registry.settings import settings


def get_all_devices(db_session: Session) -> list[Device]:
    stmt: SelectOfScalar = select(Device)
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
    WH_IN_MW = 1e6
    return device_capacity_mw * WH_IN_MW * hours
