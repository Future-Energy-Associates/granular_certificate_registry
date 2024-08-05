import datetime
import uuid as uuid_pkg
from typing import Literal, Optional


# Domains

valid_usage_units = Literal["Wh", "kWh", "MWh", "GWh"]
# grids = Literal["GB"]
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


class ForeignDeviceId(uuid_pkg.UUID):
    default: Optional[uuid_pkg.UUID] = None
    title: str = "Unique Device ID"
    description: str = ""
    foreign_key: "device.device_id"


class ForeignOrganisationId(uuid_pkg.UUID):
    default: Optional[uuid_pkg.UUID] = None
    title: str = "Unique Organisation ID"
    description: str = ""
    foreign_key: "organisation.organisation_id"


class ForeignUserId(uuid_pkg.UUID):
    default: Optional[uuid_pkg.UUID] = None
    title: str = "Unique User ID"
    description: str = ""
    foreign_key: "user.user_id"


class ForeignAccountId(uuid_pkg.UUID):
    default: Optional[uuid_pkg.UUID] = None
    title: str = "Unique Account ID"
    description: str = ""
    foreign_key: "account.account_id"


class IntervalStartDatetime(datetime.datetime):
    default: str = "2022-01-01 00:00"
    title: str = "Interval Start Datetime"
    description: str = ""


class IntervalEndDatetime(datetime.datetime):
    default: str = "2022-01-01 00:30"
    title: str = "Interval End Datetime"
    description: str = ""


class IntervalUsage(int):
    default: int = 230
    title: str = "Interval Usage"
    description: str = ""


class UsageUnits(str):
    default: str = "kWh"
    title: str = "Usage Units"
    description: str = ""


class DeviceName(str):
    default: str = ""
    title: str = "Device Name"
    description: str = ""


class OperationalDate(datetime.date):
    default: datetime.date = ""
    title: str = "Operational Date"
    description: str = ""


class Capacity(float):
    default: float = 1
    title: str = "Device Capacity"
    description: str = "This is the nameplate capacity in kW"


class PeakDemand(float):
    default: float = 1
    title: str = "Peak Demand"
    description: str = "The peak demand that has been recorded for the device"
