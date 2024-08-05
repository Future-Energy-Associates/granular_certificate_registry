from typing import List, Optional

from datamodel.schemas import entities, items
from sqlmodel import SQLModel


class RegisteringDeviceWrite(SQLModel):
    location_of_device: entities.LocationBase
    meters: List[entities.MeterBase]
    account: entities.AccountBase
    device_name: items.DeviceName
    # production_account:
    grid: str
    auxiliary_units: Optional[List[entities.DeviceBase]]
    energy_source: items.energy_sources
    technology_type: items.technology_types
    operational_date: items.OperationalDate
    subsidy_support: Optional[List[entities.SubsidySupportBase]]
    images: Optional[List[entities.ImageBase]]
    capacity: items.Capacity
    peak_demand: items.PeakDemand


class RegisteringDeviceRead(entities.DeviceRead):
    pass
