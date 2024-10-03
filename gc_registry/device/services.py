from sqlalchemy import select
from sqlmodel import Session
from gc_registry.certificate.models import GranularCertificateBundle

from gc_registry.device.models import Device


def get_device_capacity_by_id(db_session: Session, device_id: int) -> float:
    stmt = select(Device.capacity).where(Device.id == device_id)

    device_capacity = db_session.exec(stmt).first()

    return float(device_capacity[0])


def device_mw_capacity_to_wh_max(device_capacity_mwh: float, hours: float = 0.5):
    """Take the device capacity in MW and calculate the maximum Watt-Hours
    the device can produce in a given number of hours"""
    return device_capacity_mwh * 1000 * hours
