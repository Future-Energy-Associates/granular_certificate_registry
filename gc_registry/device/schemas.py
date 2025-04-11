import datetime

from sqlmodel import Field

from gc_registry import utils
from gc_registry.core.models.base import DeviceTechnologyType, EnergySourceType


class DeviceBase(utils.ActiveRecord):
    device_name: str
    local_device_identifier: str | None = Field(
        default=None,
        description="""A unique identifier for the device, ideally used by the juristiction's grid operator to identify the device
                       and link it to available data sources. This could be a meter number, a serial number, or other appropriate identifier""",
    )
    grid: str
    energy_source: EnergySourceType
    technology_type: DeviceTechnologyType
    operational_date: datetime.datetime
    capacity: float
    peak_demand: float
    location: str
    is_storage: bool
