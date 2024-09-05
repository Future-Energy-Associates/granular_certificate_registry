import datetime
from typing import Literal

# Domains

valid_usage_units = Literal["Wh", "kWh", "MWh", "GWh"]
gc_issue_device_types = Literal["production", "storage"]
energy_carriers = Literal["electricity", "natural_gas", "hydrogen", "ammonia"]
energy_sources = Literal["coal", "gas", "hydro", "hydro", "wind", "solar", "nuclear"]
technology_types = Literal[
    "recip", "ocgt", "ccgt", "coal", "offshore_wind", "onshore_wind", "solar", "nuclear"
]

certificate_actions = Literal[
    "transfer", "recurring_transfer", "cancel", "claim", "withdraw"
]
cancellation_cascade_orders = Literal["age", "price"]


# Items
class IntervalStartDatetime(datetime.datetime):
    default: datetime.datetime | None = None
    title: str = "Interval Start Datetime"
    description: str = ""


class IntervalEndDatetime(datetime.datetime):
    default: datetime.datetime | None = None
    title: str = "Interval End Datetime"
    description: str = ""


class IntervalUsage(int):
    default: int = 230
    title: str = "Interval Usage"
    description: str = ""


class UsageUnits:
    default: str = "kWh"
    title: str = "Usage Units"
    description: str = ""


class DeviceName:
    default: str | None = None
    title: str = "Device Name"
    description: str = ""


class OperationalDate(datetime.date):
    default: datetime.date | None = None
    title: str = "Operational Date"
    description: str = ""


class Capacity(float):
    default: float | None = None
    title: str = "Device Capacity"
    description: str = "This is the nameplate capacity in kW"


class PeakDemand(float):
    default: float | None = None
    title: str = "Peak Demand"
    description: str = "The peak demand that has been recorded for the device"
