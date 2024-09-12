from datetime import datetime, timedelta
from uuid import uuid4

import elexonpy
import pandas as pd
import requests
from elexonpy.api_client import ApiClient
from pydantic import UUID4

from src.datamodel.schemas.gc_entities import GranularCertificateBundle


def datetime_to_settlement_period(dt: datetime) -> int:
    return (dt.hour * 60 + dt.minute) // 30 + 1


class ElexonClient:
    def __init__(self):
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.client = ApiClient()
        self.bm_client_dynamic = elexonpy.BalancingMechanismDynamicApi()

    def get_bm_physical_data_in_datetime_range(
        self,
        from_date: datetime,
        to_date: datetime,
        bmu_ids: list[str] | None = None,
    ):
        data = []
        for half_hour_dt in pd.date_range(from_date, to_date, freq="30min"):
            settlement_period = datetime_to_settlement_period(half_hour_dt)
            if bmu_ids:
                response = self.bm_client_dynamic.balancing_dynamic_all_get(
                    half_hour_dt.date(), settlement_period, bm_unit=bmu_ids
                )
            else:
                response = self.bm_client_dynamic.balancing_dynamic_all_get(
                    half_hour_dt.date(), settlement_period
                )
            data.append(response)

        return data

    def get_dataset_in_datetime_range(
        self,
        dataset,
        from_date: datetime,
        to_date: datetime,
        bmu_ids: list[str] | None = None,
    ):
        data = []
        for half_hour_dt in pd.date_range(from_date, to_date, freq="30min"):
            params = {
                "settlementDate": half_hour_dt.date(),
                "settlementPeriod": datetime_to_settlement_period(half_hour_dt),
            }
            if bmu_ids:
                params["bmUnit"] = bmu_ids
            response = requests.get(
                f"{self.base_url}/datasets/{dataset}", params=params
            )

            response.raise_for_status()

            data.extend(response.json()["data"])

        return data

    def map_generation_to_certificates(
        self,
        generation_data: list[dict],
        account_id: UUID4,
        device_id: str | None = None,
    ) -> list[GranularCertificateBundle]:
        # Filter out any rows where the quantity is less than or equal to zero (no generation)
        generation_data = [x for x in generation_data if x["quantity"] > 0]

        mapped_data = []
        for data in generation_data:
            bundle_mwh = data["quantity"]

            # Get existing "bundle_id_range_end" from the last item in mapped_data
            if mapped_data:
                bundle_id_range_start = mapped_data[-1].bundle_id_range_end + 1
            else:
                bundle_id_range_start = 0

            bundle_id_range_end = bundle_id_range_start + bundle_mwh

            transformed = {
                "account_id": account_id,
                "certificate_status": "Active",
                "bundle_id_range_start": bundle_id_range_start,
                "bundle_id_range_end": bundle_id_range_end,
                "bundle_quantity": bundle_mwh,
                "energy_carrier": "Electricity",
                "energy_source": "wind",
                "face_value": bundle_mwh,
                "issuance_post_energy_carrier_conversion": False,
                "registry_configuration": 1,
                ### Production Device Characteristics ###
                "device_id": device_id if device_id else str(uuid4()),
                "device_name": "Device Name Placeholder",
                "device_technology_type": "wind",
                "device_production_start_date": datetime.strptime(
                    "2015-01-01", "%Y-%m-%d"
                ).date(),
                "device_capacity": 200,  # :TODO: Get the actual capacity for the BMUID
                "device_location": (0.0, 0.0),
                "device_type": "wind",
                "production_starting_interval": datetime.fromisoformat(
                    data["halfHourEndTime"]
                ),
                "production_ending_interval": datetime.fromisoformat(
                    data["halfHourEndTime"]
                ),  # Assuming half-hour interval
                "issuance_datestamp": datetime.utcnow().date(),
                "expiry_datestamp": (
                    datetime.utcnow() + timedelta(days=365 * 3)
                ).date(),
                "country_of_issuance": "Great Britain",
                "connected_grid_identification": "National Grid",
                "issuing_body": "Ofgem",
                "issue_market_zone": "Great Britain",
                "emissions_factor_production_device": 0.0,
                "emissions_factor_source": "Some Data Source",
            }

            # Validate and append the transformed data
            valid_data = GranularCertificateBundle(**transformed)
            mapped_data.append(valid_data)

        return mapped_data


if __name__ == "__main__":
    client = ElexonClient()
    from_date = datetime(2021, 1, 1, 0, 0, 0)
    to_date = from_date + pd.Timedelta(hours=2)

    # For BMU IDs see https://osuked.github.io/Power-Station-Dictionary/dictionary.html
    bmu_ids = [
        "E_MARK-1",
        "E_MARK-2",
        "RATS-1",
        "RATS-2",
        "RATS-3",
        "RATS-4",
        "RATSGT-2",
        "RATSGT-4",
    ]
    dataset = "B1610"
    data = client.get_dataset_in_datetime_range(
        dataset, from_date, to_date, bmu_ids=bmu_ids
    )
    certificates = client.map_generation_to_certificates(data)
