import logging
from datetime import date, datetime, timedelta
from typing import Any

import httpx
import pandas as pd

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.device.meter_data.abstract_client import MeterDataClient
from gc_registry.settings import settings


def datetime_to_settlement_period(dt: datetime) -> int:
    return (dt.hour * 60 + dt.minute) // 30 + 1


class ElexonClient(MeterDataClient):
    def __init__(self):
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"

    def get_dataset_in_datetime_range(
        self,
        dataset,
        from_datetime: datetime,
        to_datetime: datetime,
        bmu_ids: list[str] | None = None,
        frequency: str = "30min",
    ) -> list[dict[str, Any]]:
        """
        Get the dataset in the given date range
        e.g. https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/B1610

        Args:
            dataset: The dataset to query
            from_date: The start date
            to_date: The end date
            bmu_ids: The BMU IDs to query

        Returns:
            The dataset in the given date range
        """
        data = []
        for half_hour_dt in pd.date_range(from_datetime, to_datetime, freq=frequency):
            params = {
                "settlementDate": half_hour_dt.date(),
                "settlementPeriod": datetime_to_settlement_period(half_hour_dt),
            }
            if bmu_ids:
                params["bmUnit"] = bmu_ids

            try:
                response = httpx.get(
                    f"{self.base_url}/datasets/{dataset}",
                    params=params,  # type: ignore
                )

                response.raise_for_status()

                data.extend(response.json()["data"])
            except Exception as e:
                print(f"Error fetching data for {half_hour_dt} for {bmu_ids}: {e}")

        return data

    def resample_hh_data_to_hourly(self, data_hh_df: pd.DataFrame) -> pd.DataFrame:
        data_hh_df["start_time"] = pd.to_datetime(
            data_hh_df.halfHourEndTime
        ) - pd.Timedelta(minutes=30)

        data_resampled_concat = []
        for bmu_unit in data_hh_df.bmUnit.unique():
            data_resampled_values = (
                data_hh_df[data_hh_df.bmUnit == bmu_unit]
                .set_index("start_time")
                .quantity.resample("h")
                .sum()
            )
            data_resampled_values.name = bmu_unit
            data_resampled_concat.append(data_resampled_values)

        data_resampled = (
            pd.concat(data_resampled_concat, axis=1)
            .melt(ignore_index=False, var_name="bmUnit", value_name="quantity")
            .reset_index()
        )

        return data_resampled

    def get_asset_dataset_in_datetime_range(
        self,
        dataset,
        from_date: date,
        to_date: date,
    ):
        params = {
            "publishDateTimeFrom": from_date,
            "publishDateTimeTo": to_date,
        }
        response = httpx.get(
            f"{self.base_url}/datasets/{dataset}",
            params=params,  # type: ignore
        )

        response.raise_for_status()

        return response.json()

    def get_generation_by_device_in_datetime_range(
        self,
        from_datetime: datetime,
        to_datetime: datetime,
        meter_data_id: str,
        dataset="B1610",
    ) -> list[dict[str, Any]]:
        data = self.get_dataset_in_datetime_range(
            dataset=dataset,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            bmu_ids=[meter_data_id],
        )

        return data

    def map_generation_to_certificates(
        self,
        generation_data: list[dict[str, Any]],
        bundle_id_range_start: int,
        account_id: int,
        device_id: int,
        is_storage: bool,
        issuance_metadata_id: int,
    ) -> list[GranularCertificateBundle]:
        WH_IN_MWH = 1e6

        mapped_data: list = []
        for data in generation_data:
            bundle_wh = int(data["quantity"] * WH_IN_MWH)

            logging.info(f"Data: {data}, Bundle WH: {bundle_wh}")

            # Get existing "bundle_id_range_end" from the last item in mapped_data
            if mapped_data:
                bundle_id_range_start = mapped_data[-1].bundle_id_range_end + 1

            bundle_id_range_end = bundle_id_range_start + bundle_wh

            transformed = {
                "account_id": account_id,
                "certificate_status": "Active",
                "bundle_id_range_start": bundle_id_range_start,
                "bundle_id_range_end": bundle_id_range_end,
                "bundle_quantity": bundle_id_range_end - bundle_id_range_start + 1,
                "energy_carrier": "Electricity",
                "energy_source": "wind",
                "face_value": bundle_wh,
                "issuance_post_energy_carrier_conversion": False,
                "device_id": device_id,
                "production_starting_interval": datetime.fromisoformat(
                    data["halfHourEndTime"]
                )
                - timedelta(minutes=30),
                "production_ending_interval": datetime.fromisoformat(
                    data["halfHourEndTime"]
                ),
                "issuance_datestamp": datetime.utcnow().date(),
                "expiry_datestamp": (
                    datetime.utcnow()
                    + timedelta(days=365 * settings.CERTIFICATE_EXPIRY_YEARS)
                ).date(),
                "hash": "Some Hash",
                "metadata_id": issuance_metadata_id,
                "is_storage": is_storage,
            }

            # Validate and append the transformed data
            valid_data = GranularCertificateBundle.model_validate(transformed)
            mapped_data.append(valid_data)

        return mapped_data

    def get_device_capacities(
        self,
        bmu_ids: list[str],
        dataset: str = "IGCPU",
        from_datetime: datetime | None = None,
        to_datetime: datetime | None = None,
    ) -> dict[str, Any]:
        if from_datetime is None or to_datetime is None:
            to_datetime = datetime.now().date()
            from_datetime = to_datetime - timedelta(days=2 * 365)

        data = self.get_asset_dataset_in_datetime_range(
            dataset, from_datetime, to_datetime
        )

        df = pd.DataFrame(data["data"])

        df.sort_values("effectiveFrom", inplace=True, ascending=True)
        df.drop_duplicates(subset=["registeredResourceName"], inplace=True, keep="last")
        df = df[df.bmUnit.notna()]

        # Filter by bmu_ids
        df = df[df.bmUnit.str.contains("|".join(bmu_ids))]
        df = df[["bmUnit", "installedCapacity"]]
        df["installedCapacity"] = df["installedCapacity"].astype(int)

        # check if all bmu_ids are in the data
        if len(df) != len(bmu_ids):
            missing_bmu_ids = set(bmu_ids) - set(df["bmUnit"])
            raise ValueError(f"Missing BMU IDs: {missing_bmu_ids}")

        device_dictionary = df.to_dict(orient="records")
        device_capacities = {
            str(device["bmUnit"]): device["installedCapacity"]
            for device in device_dictionary
        }

        return device_capacities


if __name__ == "__main__":
    client = ElexonClient()

    from_datetime = datetime(2024, 1, 1, 0, 0, 0)
    to_datetime = from_datetime + timedelta(days=1)
    bmu_ids = [
        "T_RATS-1",
        "T_RATS-2",
        "T_RATS-3",
        "T_RATS-4",
        "T_RATSGT-2",
        "T_RATSGT-4",
    ]

    client.get_sp_dataset_in_datetime_range(
        "B1610", from_datetime, to_datetime, bmu_ids
    )
