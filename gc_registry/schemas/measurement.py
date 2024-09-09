import datetime

from sqlmodel import Field

from gc_registry.models.measurement import MeasurementReportBase


class MeasurementReport(MeasurementReportBase, table=True):
    id: int = Field(primary_key=True, autoincrement=True)


class MeasurementReportRead(MeasurementReportBase):
    id: int


class MeasurementReportUpdate(MeasurementReportBase):
    device_id: int | None
    interval_start_datetime: datetime.datetime | None
    interval_end_datetime: datetime.datetime | None
