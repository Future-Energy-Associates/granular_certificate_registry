import datetime
from typing import TYPE_CHECKING

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
    device_name: str | None
    grid: str | None
    energy_source: str | None
    technology_type: str | None
    operational_date: datetime.datetime | None
    capacity: float | None
    peak_demand: float | None
    location: str | None
    account_id: int | None
