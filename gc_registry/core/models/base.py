import datetime
import enum
import uuid
from enum import Enum
from functools import partial

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field

utc_datetime_now = partial(datetime.datetime.now, datetime.timezone.utc)


class UserRoles(int, Enum):
    ADMIN = 4
    PRODUCTION_USER = 3
    TRADING_USER = 2
    AUDIT_USER = 1

    def __str__(self):
        return self.name.lower()


class DeviceTechnologyType(str, enum.Enum):
    solar_pv = "solar_pv"
    wind_turbine = "wind_turbine"
    hydro = "hydro"
    battery_storage = "battery_storage"
    ev_charger = "ev_charger"
    chp = "chp"
    other = "other"


class EnergyCarrierType(str, enum.Enum):
    electricity = "electricity"
    natural_gas = "natural_gas"
    hydrogen = "hydrogen"
    heat = "heat"
    other = "other"


class EnergySourceType(str, enum.Enum):
    solar_pv = "solar_pv"
    wind = "wind"
    hydro = "hydro"
    biomass = "biomass"
    nuclear = "nuclear"
    electrolysis = "electrolysis"
    geothermal = "geothermal"
    battery_storage = "battery_storage"
    chp = "chp"
    other = "other"


class CertificateStatus(str, Enum):
    ACTIVE = "Active"
    CANCELLED = "Cancelled"
    CLAIMED = "Claimed"
    EXPIRED = "Expired"
    WITHDRAWN = "Withdrawn"
    LOCKED = "Locked"
    RESERVED = "Reserved"
    BUNDLE_SPLIT = "Bundle Split"


class CertificateActionType(str, Enum):
    TRANSFER = "transfer"
    RECURRING_TRANSFER = "recurring_transfer"
    CANCEL = "cancel"
    RECURRING_CANCEL = "recurring_cancel"
    CLAIM = "claim"
    RECURRING_CLAIM = "recurring_claim"
    WITHDRAW = "withdraw"
    LOCK = "lock"
    RESERVE = "reserve"


class EventTypes(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class Event(BaseModel):
    entity_id: int | uuid.UUID
    entity_name: str
    attributes_before: dict | None = Field(sa_column=Column(JSON))
    attributes_after: dict | None = Field(sa_column=Column(JSON))
    timestamp: datetime.datetime = Field(default_factory=utc_datetime_now)  # type: ignore


class logging_levels(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingLevelRequest(BaseModel):
    level: logging_levels
