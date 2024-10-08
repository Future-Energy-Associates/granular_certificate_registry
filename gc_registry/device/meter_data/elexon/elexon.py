from datetime import datetime, timedelta

import httpx
import pandas as pd

from gc_registry.certificate.models import GranularCertificateBundle


def datetime_to_settlement_period(dt: datetime) -> int:
    return (dt.hour * 60 + dt.minute) // 30 + 1


class ElexonClient:
    def __init__(self):
        self.base_url = "https://data.elexon.co.uk/bmrs/api/v1"

    def get_dataset_in_datetime_range(
        self,
        dataset,
        from_date: datetime,
        to_date: datetime,
        bmu_ids: list[str] | None = None,
    ):
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
        for half_hour_dt in pd.date_range(from_date, to_date, freq="30min"):
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

        return pd.DataFrame(data)

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

    def map_generation_to_certificates(
        self,
        generation_data: pd.DataFrame,
        account_id: int,
        device_id: str | None = None,
    ) -> list[GranularCertificateBundle]:
        # Filter out any rows where the quantity is less than or equal to zero (no generation)
        generation_data = generation_data.loc[generation_data["quantity"] > 0]

        mapped_data: list = []
        for _idx, data in generation_data.iterrows():
            bundle_wh = int(data["quantity"] * 1000)

            # Get existing "bundle_id_range_end" from the last item in mapped_data
            if mapped_data:
                bundle_id_range_start = mapped_data[-1].bundle_id_range_end + 1
            else:
                bundle_id_range_start = 0

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
                "registry_configuration": 1,
                ### Production Device Characteristics ###
                "device_id": device_id,
                "device_name": "Device Name Placeholder",
                "device_technology_type": "wind",
                "device_production_start_date": datetime.strptime(
                    "2015-01-01", "%Y-%m-%d"
                ).date(),
                "device_capacity": 200,  # :TODO: Get the actual capacity for the BMUID
                "device_location": (0.0, 0.0),
                "device_type": "wind",
                "production_starting_interval": data["start_time"],
                "production_ending_interval": data["start_time"] + timedelta(hours=1),
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
                "hash": "Some Hash",
            }

            # Validate and append the transformed data
            valid_data = GranularCertificateBundle.model_validate(transformed)
            mapped_data.append(valid_data)

        return mapped_data
