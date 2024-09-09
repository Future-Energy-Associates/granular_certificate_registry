import datetime
import uuid as uuid_pkg
from typing import (
    Optional,
)

from sqlmodel import Field

from src.models.measurement import MeasurementReportBase


class MeasurementReport(MeasurementReportBase, table=True):
    measurement_report_id: uuid_pkg.UUID = Field(
        primary_key=True, default_factory=uuid_pkg.uuid4
    )


class MeasurementReportRead(MeasurementReportBase):
    measurement_report_id: uuid_pkg.UUID


class MeasurementReportUpdate(MeasurementReportBase):
    measurement_report_id: Optional[uuid_pkg.UUID]
    interval_start_datetime: Optional[datetime.datetime]
    interval_end_datetime: Optional[datetime.datetime]
