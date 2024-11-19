import logging
from datetime import date, datetime, timedelta
from typing import Any

import httpx
import pandas as pd

from gc_registry.core.models.base import (
    CertificateStatus,
    EnergyCarrierType,
    EnergySourceType,
)
from gc_registry.settings import settings


def datetime_to_settlement_period(dt: datetime) -> int:
    return (dt.hour * 60 + dt.minute) // 30 + 1

psr_type_renewable_flag = {
    "Wind Offshore":True,
    "Generation":False,
    "Other":False,
    "Wind Onshore":True,
    "Fossil Gas":False,
    "Fossil Oil":False,
    "Hydro Run-of-river and poundage":True,
    "Biomass":True,
    "Fossil Hard coal":False,
    "Hydro Water Reservoir":True,
    "Nuclear":True,
    "Other renewable":True,
    "Solar":True,
}

psr_type_to_energy_source = {
        "Wind Offshore":"wind",
    "Generation":"other",
    "Other":"other",
    "Wind Onshore":"wind",
    "Fossil Gas":"gas",
    "Fossil Oil":"oil",
    "Hydro Run-of-river and poundage":"hydro",
    "Biomass":"biomass",
    "Fossil Hard coal":"coal",
    "Hydro Water Reservoir":"hydro",
    "Nuclear":"nuclear",
    "Other renewable":"other renewable",
    "Solar":"solar",
}

class ElexonClient:
    def __init__(self):
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"
        self.renewable_psr_types = [k for k,v in psr_type_renewable_flag.items() if v]
        self.psr_type_to_energy_source = psr_type_to_energy_source

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

    def resample_hh_data_to_hourly(
        self, data_hh_df: pd.DataFrame
    ) -> list[dict[str, Any]]:

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

        return data_resampled.to_dict(orient="records")

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

    def get_metering_by_device_in_datetime_range(
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

        print(f"Data for {meter_data_id}: {len(data)}")
        if not data:
            return []

        meter_data_df = pd.DataFrame(data)
        data = self.resample_hh_data_to_hourly(meter_data_df)

        return data

    def map_metering_to_certificates(
        self,
        generation_data: list[dict[str, Any]],
        account_id: int,
        device_id: int,
        is_storage: bool,
        issuance_metadata_id: int,
        bundle_id_range_start: int = 0,
    ) -> list[dict[str, Any]]:
        WH_IN_MWH = 1e6

        mapped_data: list = []
        for data in generation_data:
            bundle_wh = int(data["quantity"] * WH_IN_MWH)

            if bundle_wh <= 0:
                continue

            logging.info(f"Data: {data}, Bundle WH: {bundle_wh}")

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
                "bundle_quantity": bundle_wh,
                "energy_carrier": EnergyCarrierType.electricity,
                "energy_source": EnergySourceType.wind,
                "face_value": 1,
                "issuance_post_energy_carrier_conversion": False,
                "device_id": device_id,
                "production_starting_interval": data["start_time"],
                "production_ending_interval": data["start_time"]
                + pd.Timedelta(minutes=60),
                "issuance_datestamp": datetime.utcnow().date(),
                "expiry_datestamp": (
                    datetime.utcnow()
                    + timedelta(days=365 * settings.CERTIFICATE_EXPIRY_YEARS)
                ).date(),
                "metadata_id": issuance_metadata_id,
                "is_storage": is_storage,
                "hash": "Some hash",
            }

            transformed["issuance_id"] = (
                f"{device_id}-{transformed['production_starting_interval']}"
            )

            mapped_data.append(transformed)

        return mapped_data

    def get_device_capacities(
        self,
        bmu_ids: list[str],
        from_date: date = datetime.now().date() - timedelta(days=365 * 2),
        to_date: date = datetime.now().date(),
        dataset: str = "IGCPU",
    ) -> dict[str, Any]:
        data = self.get_asset_dataset_in_datetime_range(dataset, from_date, to_date)

        df = pd.DataFrame(data["data"])

        df.sort_values("effectiveFrom", inplace=True, ascending=True)
        df.drop_duplicates(subset=["registeredResourceName"], inplace=True, keep="last")
        df = df[df.bmUnit.notna()]

        # Filter by bmu_ids
        df = df[df.bmUnit.isin(bmu_ids)]
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

    from_date = datetime.now() - timedelta(weeks=52*30)
    to_date = datetime.now()

    # Create year long ranges from the from_date to the to_date
    data_list = []
    for from_datetime in pd.date_range(from_date,to_date,freq="Y"):
        to_datetime = from_datetime + timedelta(days=365) if from_datetime + timedelta(days=365) < to_date else to_date

        print(f"Getting data from {from_datetime} to {to_datetime}")

        data = client.get_asset_dataset_in_datetime_range(
            dataset="IGCPU",
            from_date=from_datetime,
            to_date=to_datetime,
        )
        data_list.extend(data['data'])

    df = pd.DataFrame(data_list)

    df.sort_values("effectiveFrom", inplace=True, ascending=True)
    df.drop_duplicates(subset=["registeredResourceName"], inplace=True, keep="last")
    df = df[df.bmUnit.notna()]

    # drop all non-renewable psr types
    df = df[df.psrType.isin(client.renewable_psr_types)]
