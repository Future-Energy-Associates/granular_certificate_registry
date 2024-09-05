from typing import List, Optional

from sqlmodel import SQLModel

from gc_registry.datamodel.schemas import entities, items


class RegisteringDeviceWrite(SQLModel):
    location_of_device: str
    # meters: List[entities.MeterBase]
    account: entities.AccountBase
    device_name: items.DeviceName
    # production_account:
    grid: str
    auxiliary_units: Optional[List[entities.DeviceBase]]
    energy_source: items.energy_sources
    technology_type: items.technology_types
    operational_date: items.OperationalDate
    subsidy_support: str | None
    capacity: items.Capacity
    peak_demand: items.PeakDemand


class RegisteringDeviceRead(entities.DeviceRead):
    pass
