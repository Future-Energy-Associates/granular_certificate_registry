import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from gc_registry.core.models.base import DeviceTechnologyType
from gc_registry.device.schemas import DeviceBase

if TYPE_CHECKING:
    from gc_registry.account.models import Account

# Device - production, consumption, or storage, each device is associated
# with exactly one account owned by an organisation operating in the same
# domain as the Device.


class Device(DeviceBase, table=True):
    id: int | None = Field(
        default=None,
        description="A unique identifier for the device. Integers could be used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
    )
    account_id: int = Field(foreign_key="account.id")
    account: "Account" = Relationship(back_populates="devices")
    is_deleted: bool = Field(default=False)


class DeviceRead(DeviceBase):
    id: int


class DeviceUpdate(SQLModel):
    id: int | None = None
    device_name: str | None = None
    grid: str | None = None
    energy_source: str | None = None
    technology_type: DeviceTechnologyType | None = None
    operational_date: datetime.datetime | None = None
    capacity: float | None = None
    peak_demand: float | None = None
    location: str | None = None
    account_id: int | None = None
