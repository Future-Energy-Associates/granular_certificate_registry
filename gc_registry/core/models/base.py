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
