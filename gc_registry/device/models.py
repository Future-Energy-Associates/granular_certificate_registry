import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Field, Relationship

from gc_registry.core.models.base import DeviceTechnologyType
from gc_registry.device.schemas import DeviceBase

if TYPE_CHECKING:
    from gc_registry.account.models import Account

# Device - production, consumption, or storage, each device is associated
# with exactly one account owned by an organisation operating in the same
# domain as the Device.


class Device(DeviceBase, table=True):
    id: int = Field(
        description="A unique identifier for the device. Integers could be used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
    )
    account: "Account" = Relationship(back_populates="devices")


class DeviceRead(DeviceBase):
    id: int


class DeviceUpdate(BaseModel):
    id: int
    device_name: str | None
    grid: str | None
    energy_source: str | None
    technology_type: DeviceTechnologyType | None
    operational_date: datetime.datetime | None
    capacity: float | None
    peak_demand: float | None
    location: str | None
    account_id: int | None
