import datetime
from typing import (
    TYPE_CHECKING,
    Optional,
)

from sqlmodel import Field, Relationship

from gc_registry.models.device import DeviceBase

if TYPE_CHECKING:
    from gc_registry.schemas.account import Account

# Device - production, consumption, or storage, each device is associated
# with exactly one account owned by an organisation operating in the same
# domain as the Device.


class Device(DeviceBase, table=True):
    device_id: int = Field(
        description="A unique identifier for the device. UUIDv4 could be used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
        autoincrement=True,
    )
    account: "Account" = Relationship(back_populates="devices")


class DeviceRead(DeviceBase):
    device_id: int


class DeviceUpdate(DeviceBase):
    device_name: Optional[str]
    grid: Optional[str]
    energy_source: Optional[str]
    technology_type: Optional[str]
    operational_date: Optional[datetime.datetime]
    capacity: Optional[float]
    peak_demand: Optional[float]
    location: Optional[str]
    account_id: Optional[int]
