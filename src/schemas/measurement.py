import datetime
import uuid as uuid_pkg
from typing import (
    Optional,
)

from sqlmodel import Field

from src.schemas import utils


class MeasurementReportBase(utils.ActiveRecord):
    device_id: uuid_pkg.UUID
    interval_start_datetime: datetime.datetime
    interval_end_datetime: datetime.datetime
    interval_usage: int = Field(
        description="The quantity of energy consumed, produced, or stored in Wh by the device during the specified interval.",
    )
    gross_net_indicator: str = Field(
        description="Indicates whether the usage is gross or net of any losses in the system.",
    )


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
