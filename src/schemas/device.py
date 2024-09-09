import datetime
import uuid as uuid_pkg
from typing import (
    ForwardRef,
    Optional,
)

from sqlmodel import Field, Relationship

from src.models.device import DeviceBase

# Device - production, consumption, or storage, each device is associated
# with exactly one account owned by an organisation operating in the same
# domain as the Device.

Account = ForwardRef("Account", module="src.schemas.account")


class Device(DeviceBase, table=True):
    device_id: uuid_pkg.UUID = Field(
        description="A unique identifier for the device. UUIDv4 could be used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
        default_factory=uuid_pkg.uuid4,
    )
    account: Account = Relationship(back_populates="devices")


class DeviceRead(DeviceBase):
    device_id: uuid_pkg.UUID


class DeviceUpdate(DeviceBase):
    device_id: Optional[uuid_pkg.UUID]
    device_name: Optional[str]
    account: Optional[Account]
    grid: Optional[str]
    energy_source: Optional[str]
    technology_type: Optional[str]
    operational_date: Optional[datetime.date]
    capacity: Optional[float]
    peak_demand: Optional[float]
    location: Optional[str]
