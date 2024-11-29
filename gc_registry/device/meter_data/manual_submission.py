import datetime
from typing import Any

from sqlalchemy.sql.expression import select
from sqlmodel import Session

from gc_registry.core.models.base import (
    CertificateStatus,
    EnergyCarrierType,
)
from gc_registry.device.meter_data.abstract_meter_client import AbstractMeterDataClient
from gc_registry.device.models import Device
from gc_registry.logging_config import logger
from gc_registry.measurement.models import MeasurementReport
from gc_registry.settings import settings


class ManualSubmissionMeterClient(AbstractMeterDataClient):
    def __init__(self):
        self.NAME = "ManualSubmissionMeterClient"

    def get_metering_by_device_in_datetime_range(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
        device_id: int,
        read_session: Session,
    ) -> list[MeasurementReport] | None:
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

        meter_records = read_session.exec(stmt).all()  # type: ignore

        if not meter_records:
            logger.error(
                f"No meter records found for device {device_id} in the specified time range."
            )
            return None

        meter_records = [meter[0] for meter in meter_records]

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
        """Map meter records to certificate bundles.

        Args:
            generation_data (list[MeasurementReport]): A list of meter records taken from the database.
            account_id (int): The ID of the account to which the certificate bundles will be issued.
            device (Device): The device for which the meter records were taken.
            is_storage (bool): Whether the device is a storage device.
            issuance_metadata_id (int): The ID of the issuance metadata associated with these records.
            bundle_id_range_start (int): The starting ID of the bundle range, if not zero.

        Returns:
            list[dict[str, Any]]: A list of dictionaries containing the certificate bundle data.
        """

        mapped_data: list = []

        for data in generation_data:
            # Get existing "bundle_id_range_end" from the last item in mapped_data
            if mapped_data:
                bundle_id_range_start = mapped_data[-1]["bundle_id_range_end"] + 1

            # E.g., if bundle_wh = 1000, bundle_id_range_start = 0, bundle_id_range_end = 999
            # TODO this breaks for a bundle of 1 Wh as bundle_id_range_end = bundle_id_range_start
            bundle_id_range_end = bundle_id_range_start + data.interval_usage - 1

            transformed = {
                "account_id": account_id,
                "certificate_bundle_status": CertificateStatus.ACTIVE,
                "bundle_id_range_start": bundle_id_range_start,
                "bundle_id_range_end": bundle_id_range_end,
                "bundle_quantity": bundle_id_range_end - bundle_id_range_start + 1,
                "energy_carrier": EnergyCarrierType.electricity,
                "energy_source": device.energy_source,
                "face_value": 1,
                "issuance_post_energy_carrier_conversion": False,
                "device_id": device.id,
                "production_starting_interval": data.interval_start_datetime,
                "production_ending_interval": data.interval_end_datetime,
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
