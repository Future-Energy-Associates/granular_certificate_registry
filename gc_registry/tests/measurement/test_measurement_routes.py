

from unittest.mock import MagicMock
import pandas as pd
import pytest


@pytest.fixture
def valid_measurement_json():

    return """
    [
        {"device_id": "device_1", "interval_usage": 10, "interval_start_datetime": "2024-11-18T10:00:00", "interval_end_datetime": "2024-11-18T11:00:00"},
        {"device_id": "device_1", "interval_usage": 15, "interval_start_datetime": "2024-11-18T11:00:00", "interval_end_datetime": "2024-11-18T12:00:00"},
        {"device_id": "device_2", "interval_usage": 20, "interval_start_datetime": "2024-11-18T10:00:00", "interval_end_datetime": "2024-11-18T11:00:00"}
    ]
    """


def test_submit_readings_success(api_client, db_write_session, db_read_session, esdb_client, valid_measurement_json, parsed_measurement_df, monkeypatch
):
    """Test successful submission of readings."""

    response = api_client.post(
        "measurement/submit_readings/",
        json={"measurement_json": valid_measurement_json},
    )

    print(response.json())

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["message"] == "Readings submitted successfully."
    assert response_data["total_usage_per_device"] == {"device_1": 25, "device_2": 20}
    assert response_data["first_reading_datetime"] == "2024-11-18T10:00:00"
    assert response_data["last_reading_datetime"] == "2024-11-18T12:00:00"
