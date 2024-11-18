import json

import pandas as pd


def serialise_measurement_csv(measurement_csv_path: str) -> str:
    """Read a CSV file from the path provided into a pandas DataFrame and serialize to a JSON string.

    Asserts that the column names are 'device_id', 'interval_start_datetime', 'interval_end_datetime and 'interval_usage'.

    Args:
        measurement_csv_path (str): The path to the CSV file.

    Returns:
        str: A column-oriented JSON string representation of the data.
    """

    data = pd.read_csv(measurement_csv_path)
    assert all(
        col in data.columns
        for col in [
            "device_id",
            "interval_start_datetime",
            "interval_end_datetime",
            "interval_usage",
            "gross_net_indicator",
        ]
    ), "Dataframe columns must be 'device_id', 'interval_start_datetime', 'interval_usage', 'gross_net_indicator'"

    return data.to_json(orient="columns")


def parse_measurement_json(
    recieved_json: str, to_df: bool = False
) -> dict | pd.DataFrame:
    """Take a measurement JSON string and parse it into a dict or a Pandas DataFrame.

    Asserts that the column names are 'device_id', 'interval_start_datetime', 'interval_end_datetime and 'interval_usage'.

    Args:
        recieved_json (str): A JSON string representation of the data.
        to_df (bool, optional): If True, return the data as a pandas DataFrame.

    Returns:
        pd.DataFrame: A pandas DataFrame representation of the data.
    """
    raw_input = pd.DataFrame.from_dict(json.loads(recieved_json))
    assert all(
        col in raw_input.columns
        for col in [
            "device_id",
            "interval_start_datetime",
            "interval_end_datetime",
            "interval_usage",
            "gross_net_indicator",
        ]
    ), "Dataframe columns must be 'device_id', 'interval_start_datetime', 'interval_usage', 'gross_net_indicator'"

    return raw_input if to_df else raw_input.to_dict(orient="records")
