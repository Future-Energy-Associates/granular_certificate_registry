import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, Session, SQLModel, select

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
    account_id: int = Field(
        foreign_key="account.id",
        description="The account to which the device is registered, and into which GC Bundles will be issued for energy produced by this Device.",
    )
    is_deleted: bool = Field(default=False)
    account: "Account" = Relationship(back_populates="devices")

    @classmethod
    def by_name(cls, name: str, read_session: Session) -> "Device | None":
        return read_session.exec(select(cls).where(cls.device_name == name)).first()


class DeviceRead(DeviceBase):
    id: int


class DeviceCreate(DeviceBase):
    account_id: int


class DeviceUpdate(SQLModel):
    device_name: str | None = None
    grid: str | None = None
    energy_source: str | None = None
    technology_type: DeviceTechnologyType | None = None
    operational_date: datetime.datetime | None = None
    power_mw: float | None = None
    energy_mwh: float | None = None
    peak_demand: float | None = None
    location: str | None = None
    account_id: int | None = None
