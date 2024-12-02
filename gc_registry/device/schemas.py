import datetime

from sqlmodel import Field

from gc_registry import utils


class DeviceBase(utils.ActiveRecord):
    device_name: str
    meter_data_id: str | None
    grid: str
    energy_source: str
    technology_type: str
    operational_date: datetime.datetime
    capacity: float
    peak_demand: float
    location: str
    is_storage: bool
    account_id: int = Field(
        description="The account to which the device is registered, and into which GC Bundles will be issued for energy produced by this Device.",
        foreign_key="account.id",
    )
    is_deleted: bool = Field(default=False)
