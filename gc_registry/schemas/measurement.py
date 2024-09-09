import datetime
from typing import (
    Optional,
)

from sqlmodel import Field

from gc_registry.models.measurement import MeasurementReportBase


class MeasurementReport(MeasurementReportBase, table=True):
    measurement_report_id: int = Field(primary_key=True, autoincrement=True)


class MeasurementReportRead(MeasurementReportBase):
    measurement_report_id: int


class MeasurementReportUpdate(MeasurementReportBase):
    measurement_report_id: Optional[int]
    interval_start_datetime: Optional[datetime.datetime]
    interval_end_datetime: Optional[datetime.datetime]
