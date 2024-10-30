import enum
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field


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


class CertificateActionType(str, Enum):
    TRANSFER = "transfer"
    RECURRING_TRANSFER = "recurring_transfer"
    CANCEL = "cancel"
    RECURRING_CANCEL = "recurring_cancel"
    CLAIM = "claim"
    RECURRING_CLAIM = "recurring_claim"
    WITHDRAW = "withdraw"
    LOCK = "lock"


class EventTypes(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class Event(BaseModel):
    entity_id: int | uuid.UUID
    entity_name: str
    attributes_before: dict | None = Field(sa_column=Column(JSON))
    attributes_after: dict | None = Field(sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
