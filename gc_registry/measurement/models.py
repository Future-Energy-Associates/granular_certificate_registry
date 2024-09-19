import datetime

from pydantic import BaseModel
from sqlmodel import Field

from gc_registry.measurement.schemas import MeasurementReportBase


class MeasurementReport(MeasurementReportBase, table=True):
    id: int | None = Field(primary_key=True)
    is_deleted: bool = Field(default=False)


class MeasurementReportRead(MeasurementReportBase):
    id: int


class MeasurementReportUpdate(BaseModel):
    id: int | None = None
    device_id: int | None = None
    interval_start_datetime: datetime.datetime | None = None
    interval_end_datetime: datetime.datetime | None = None
