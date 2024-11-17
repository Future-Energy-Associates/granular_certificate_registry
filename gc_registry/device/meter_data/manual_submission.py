from typing import Any
from sqlmodel import Session
from gc_registry.core.models.base import (
    CertificateStatus,
    EnergyCarrierType,
    EnergySourceType,
)
from gc_registry.device.meter_data.abstract_meter_client import AbstractMeterDataClient
from gc_registry.measurement.models import MeasurementReport
from sqlalchemy.sql.expression import select
import datetime
from gc_registry.logging_config import logger
from gc_registry.device.models import Device
import pandas as pd
from gc_registry.settings import settings


class ManualSubmissionMeterClient(AbstractMeterDataClient):
    def get_metering_by_device_in_datetime_range(
        self,
        device_id: int,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
        read_session: Session,
    ) -> list[MeasurementReport]:
        """Retrieve meter records from the database for a specific device in a specific time range.

        Will raise an error if no records are found for the specified device and time range.

        Args:

            device_id (int): The ID of the device for which to retrieve meter records.
            start_datetime (datetime.datetime): The start of the time range for which to retrieve meter records.
            end_datetime (datetime.datetime): The end of the time range for which to retrieve meter records.

        Returns:

                dict: A dictionary containing the meter records.
        """

        stmt = select(MeasurementReport).filter(
            MeasurementReport.device_id == device_id,
            MeasurementReport.interval_start_datetime >= start_datetime,
            MeasurementReport.interval_end_datetime <= end_datetime,
        )

        meter_records = read_session.exec(stmt).all()

        if not meter_records:
            logger.error(
                f"No meter records found for device {device_id} in the specified time range."
            )
            return None

        return meter_records

    def map_metering_to_certificates(
        self,
        generation_data: list[MeasurementReport],
        account_id: int,
        device: Device,
        is_storage: bool,
        issuance_metadata_id: int,
        bundle_id_range_start: int = 0,
    ) -> list[dict[str, Any]]:
        WH_IN_MWH = 1e6

        mapped_data: list = []

        for data in generation_data:
            bundle_wh = int(data["interval_usage"] * WH_IN_MWH)

            logger.debug(f"Data: {data}, Bundle WH: {bundle_wh}")

            # Get existing "bundle_id_range_end" from the last item in mapped_data
            if mapped_data:
                bundle_id_range_start = mapped_data[-1]["bundle_id_range_end"] + 1

            # E.g., if bundle_wh = 1000, bundle_id_range_start = 0, bundle_id_range_end = 999
            bundle_id_range_end = bundle_id_range_start + bundle_wh - 1

            transformed = {
                "account_id": account_id,
                "certificate_status": CertificateStatus.ACTIVE,
                "bundle_id_range_start": bundle_id_range_start,
                "bundle_id_range_end": bundle_id_range_end,
                "bundle_quantity": bundle_id_range_end - bundle_id_range_start + 1,
                "energy_carrier": EnergyCarrierType.electricity,
                "energy_source": device.energy_source,
                "face_value": 1,
                "issuance_post_energy_carrier_conversion": False,
                "device_id": device.id,
                "production_starting_interval": data["start_time"],
                "production_ending_interval": data["start_time"]
                + pd.Timedelta(minutes=60),
                "issuance_datestamp": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).date(),
                "expiry_datestamp": (
                    datetime.datetime.now(tz=datetime.timezone.utc)
                    + datetime.timedelta(days=365 * settings.CERTIFICATE_EXPIRY_YEARS)
                ).date(),
                "metadata_id": issuance_metadata_id,
                "is_storage": is_storage,
                "hash": "Some hash",
            }

            transformed["issuance_id"] = (
                f"{device.id}-{transformed['production_starting_interval']}"
            )

            mapped_data.append(transformed)

        return mapped_data
