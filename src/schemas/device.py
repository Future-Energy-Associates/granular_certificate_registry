import datetime
import uuid as uuid_pkg
from typing import (
    Optional,
)

from sqlmodel import Field, Relationship

from src.schemas import utils
from src.schemas.account import Account

# Device - production, consumption, or storage, each device is associated
# with exactly one account owned by an organisation operating in the same
# domain as the Device.


class DeviceBase(utils.ActiveRecord):
    device_name: str
    grid: str
    energy_source: str
    technology_type: str
    operational_date: datetime.date
    capacity: float
    peak_demand: float
    location: str
    account_id: uuid_pkg.UUID = Field(
        description="The account to which the device is registered, and into which GC Bundles will be issued for energy produced by this Device.",
        foreign_key="account.account_id",
    )


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
