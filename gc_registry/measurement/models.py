import datetime

from pydantic import BaseModel
from sqlmodel import Field

from gc_registry.measurement.schemas import MeasurementReportBase


class MeasurementReport(MeasurementReportBase, table=True):
    id: int | None = Field(primary_key=True)


class MeasurementReportRead(MeasurementReportBase):
    id: int


class MeasurementReportUpdate(BaseModel):
    device_id: int | None = None
    interval_start_datetime: datetime.datetime | None = None
    interval_end_datetime: datetime.datetime | None = None


class MeasurementSubmissionResponse(BaseModel):
    message: str
    first_reading_datetime: datetime.datetime
    last_reading_datetime: datetime.datetime
    total_usage_per_device: dict[int, float]
