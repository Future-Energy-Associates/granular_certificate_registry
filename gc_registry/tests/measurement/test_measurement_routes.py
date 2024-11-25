import json

import pytest


@pytest.fixture
def valid_measurement_json():
    return json.dumps(
        [
            {
                "device_id": 1,
                "interval_usage": 10,
                "interval_start_datetime": "2024-11-18T10:00:00",
                "interval_end_datetime": "2024-11-18T11:00:00",
                "gross_net_indicator": "NET",
            },
            {
                "device_id": 1,
                "interval_usage": 15,
                "interval_start_datetime": "2024-11-18T11:00:00",
                "interval_end_datetime": "2024-11-18T12:00:00",
                "gross_net_indicator": "NET",
            },
            {
                "device_id": 2,
                "interval_usage": 20,
                "interval_start_datetime": "2024-11-18T10:00:00",
                "interval_end_datetime": "2024-11-18T11:00:00",
                "gross_net_indicator": "NET",
            },
        ]
    )


def test_submit_readings_success(
    api_client,
    valid_measurement_json,
):
    """Test successful submission of readings."""

    response = api_client.post(
        "measurement/submit_readings/",
        params={"measurement_json": valid_measurement_json},
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["message"] == "Readings submitted successfully."
    assert response_data["total_usage_per_device"] == {"1": 25, "2": 20}
    assert response_data["first_reading_datetime"] == "2024-11-18T10:00:00"
    assert response_data["last_reading_datetime"] == "2024-11-18T12:00:00"
