import datetime
import json
from typing import Any

import httpx
import pandas as pd

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.device.meter_data.abstract_meter_client import AbstractMeterDataClient


def mock_response(endpoint: str) -> httpx.Response:
    df = pd.read_csv(f"./src/issuance_data/pjm/{endpoint}.csv")

    response = httpx.Response(status_code=200)
    response._content = json.dumps(df.to_dict("records")).encode("utf-8")

    return response


def parse_datetime(date_str, format="%m/%d/%Y %I:%M:%S %p"):
    return datetime.datetime.strptime(date_str, format)


class PJM(AbstractMeterDataClient):
    def __init__(self):
        self.base_url = "https://dataminer2.pjm.com/feed"
        self.name = "PJM"

    def get_metering_by_device_in_datetime_range(self, endpoint: str, test=False):
        if test:
            response = mock_response(endpoint)
        else:
            response = httpx.get(f"{self.base_url}/{endpoint}")

        response.raise_for_status()

        return response

    def map_metering_to_certificates(
        self,
        generation_data: list[dict[Any, Any]],
        account_id: str | None = None,
        device_id: str | None = None,
    ) -> list[GranularCertificateBundle]:
        # drop any rows where is_renewable is False
        generation_data = [x for x in generation_data if x["is_renewable"]]

        mapped_data: list[GranularCertificateBundle] = []
        for data in generation_data:
            bundle_mwh = data["mw"] * 1000

            # get existing "bundle_id_range_end" from the last item in mapped_data
            if mapped_data:
                bundle_id_range_start = mapped_data[-1].bundle_id_range_end + 1
            else:
                bundle_id_range_start = 0

            bundle_id_range_end = bundle_id_range_start + bundle_mwh

            transformed = {
                ### Account details ###
                "account_id": account_id,
                ### Mutable Attributes ###
                "certificate_status": "Active",
                "bundle_id_range_start": bundle_id_range_start,
                "bundle_id_range_end": bundle_id_range_end,
                "bundle_quantity": bundle_mwh,
                ### Bundle Characteristics ###
                "energy_carrier": "Electricity",
                "energy_source": data["fuel_type"],
                "face_value": 1,
                "issuance_post_energy_carrier_conversion": False,
                "registry_configuration": 1,
                ### Production Device Characteristics ###
                "device_id": device_id,
                "device_name": "Device Name Placeholder",
                "device_technology_type": data["fuel_type"],
                "device_production_start_date": parse_datetime(
                    "2015-01-01 00:00:00", format="%Y-%m-%d %H:%M:%S"
                ).date(),
                "device_capacity": data["mw"] * 1000,
                "device_location": (0.0, 0.0),
                "device_type": data["fuel_type"],
                ### Temporal Characteristics ###
                "production_starting_interval": parse_datetime(
                    data["datetime_beginning_utc"]
                ),
                "production_ending_interval": parse_datetime(
                    data["datetime_beginning_utc"]
                ),  # Assuming 1-hour interval
                "issuance_datestamp": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).date(),
                "expiry_datestamp": (
                    datetime.datetime.now(tz=datetime.timezone.utc)
                    + datetime.timedelta(days=365 * 3)
                ).date(),
                ### Issuing Body Characteristics ###
                "country_of_issuance": "USA",
                "connected_grid_identification": "PJM",
                "issuing_body": "An Corp Issuing Body",
                "issue_market_zone": "PJM",
                "emissions_factor_production_device": 0.0,
                "emissions_factor_source": "Some Data Source",
            }

            valid_data = GranularCertificateBundle.model_validate(transformed)
            mapped_data.append(valid_data)

        return mapped_data

