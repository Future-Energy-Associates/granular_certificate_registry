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
class IntervalStartDatetime:
    default: datetime.datetime | None = None
    title: str = "Interval Start Datetime"
    description: str = ""


class IntervalEndDatetime:
    default: datetime.datetime | None = None
    title: str = "Interval End Datetime"
    description: str = ""


class IntervalUsage:
    default: int | None = None
    title: str = "Interval Usage"
    description: str = ""


class UsageUnits:
    default: str = "kWh"
    title: str = "Usage Units"
    description: str = ""


class DeviceName:
    default: str = ""
    title: str = "Device Name"
    description: str = ""


class OperationalDate:
    default: datetime.datetime | None = None
    title: str = "Operational Date"
    description: str = ""


class Capacity:
    default: float | None = None
    title: str = "Device Capacity"
    description: str = "This is the nameplate capacity in kW"


class PeakDemand:
    default: float | None = None
    title: str = "Peak Demand"
    description: str = "The peak demand that has been recorded for the device"
