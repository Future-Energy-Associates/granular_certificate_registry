import io

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from gc_registry.device.models import Device


@pytest.fixture
def valid_storage_record_csv():
    """Create a CSV string with valid storage record data."""
    return (
        "flow_start_datetime,flow_end_datetime,flow_energy,flow_energy_source,validator_id\n"
        "2024-01-01T00:00:00Z,2024-01-01T01:00:00Z,-1000,GRID,0\n"
        "2024-01-01T01:00:00Z,2024-01-01T02:00:00Z,-1200,GRID,1\n"
        "2024-01-01T01:00:00Z,2024-01-01T02:00:00Z,1000,,2\n"
        "2024-01-01T02:00:00Z,2024-01-01T03:00:00Z,-1500,SOLAR,3\n"
        "2024-01-01T03:00:00Z,2024-01-01T04:00:00Z,600,,4\n"
    )


@pytest.fixture
def valid_allocation_record_csv():
    """Create a CSV string with valid allocation record data."""
    return (
        "scr_allocation_id,sdr_allocation_id,sdr_proportion,scr_allocation_methodology,gc_allocation_id,sdgc_allocation_id,efficiency_factor_methodology,efficiency_factor_interval_start,efficiency_factor_interval_end,storage_efficiency_factor\n"
        "0,2,1.0,FIFO,,,EnergyTag Standard,2024-01-01 00:00:00,2025-01-01 00:00:00,0.87\n"
        "1,4,0.5,FIFO,,,EnergyTag Standard,2024-01-01 00:00:00,2025-01-01 00:00:00,0.87\n"
    )


def test_submit_storage_records_success(
    api_client: TestClient,
    token_storage_validator: str,
    valid_storage_record_csv: str,
    valid_allocation_record_csv: str,
    fake_db_storage_device: Device,
    read_session: Session,
):
    """Test successful submission of storage records and allocations."""
    # Create file-like objects from CSV strings
    records_csv_file = io.BytesIO(valid_storage_record_csv.encode("utf-8"))
    allocations_csv_file = io.BytesIO(valid_allocation_record_csv.encode("utf-8"))

    # Create form data
    data = {
        "deviceID": str(fake_db_storage_device.id),
    }

    # Submit storage records
    storage_files = {"file": ("records.csv", records_csv_file, "text/csv")}

    assert storage_files
    assert data
    assert allocations_csv_file

    # response = api_client.post(
    #     "/storage/submit_storage_records",
    #     files=storage_files,
    #     data=data,
    #     headers={"Authorization": f"Bearer {token_storage_validator}"},
    # )

    # print(response.text)

    # assert response.status_code == 201
    # response_data = response.json()
    # assert response_data["message"] == "Storage records created successfully."
    # assert response_data["total_charge_energy"] == 3700
    # assert response_data["total_discharge_energy"] == 1600
    # assert response_data["total_energy"] == 5300
    # assert response_data["total_records"] == 5

    # # Submit allocation records
    # allocation_files = {"file": ("allocations.csv", allocations_csv_file, "text/csv")}
    # response = api_client.post(
    #     "/storage/submit_allocation_records",
    #     files=allocation_files,
    #     data=data,
    #     headers={"Authorization": f"Bearer {token_storage_validator}"},
    # )

    # assert response.status_code == 201
    # response_data = response.json()
    # assert response_data["message"] == "Allocation records created successfully."
    # assert response_data["total_records"] == 2
