import datetime
import io

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from gc_registry.core.models.base import UserRoles
from gc_registry.device.models import Device
from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord


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
        "device_id": str(fake_db_storage_device.id),
    }

    # Submit storage records
    storage_files = {"file": ("records.csv", records_csv_file, "text/csv")}

    response = api_client.post(
        "/storage/storage_records",
        files=storage_files,
        data=data,
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    print(response.text)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["message"] == "Storage records created successfully."
    assert response_data["total_charge_energy"] == 3700
    assert response_data["total_discharge_energy"] == 1600
    assert response_data["total_energy"] == 5300
    assert response_data["total_records"] == 5

    # Submit allocation records
    allocation_files = {"file": ("allocations.csv", allocations_csv_file, "text/csv")}
    response = api_client.post(
        "/storage/allocated_storage_records",
        files=allocation_files,
        data=data,
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    print(response.text)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["message"] == "Allocation records created successfully."
    assert response_data["total_records"] == 2


def test_submit_storage_charge_records_success(
    api_client: TestClient,
    token_storage_validator: str,
    valid_storage_record_csv: str,
    fake_db_storage_device: Device,
    read_session: Session,
):
    """Test successful submission of storage charge records."""
    records_csv_file = io.BytesIO(valid_storage_record_csv.encode("utf-8"))

    data = {
        "device_id": str(fake_db_storage_device.id),
    }

    storage_files = {"file": ("records.csv", records_csv_file, "text/csv")}

    response = api_client.post(
        "/storage/storage_records",
        files=storage_files,
        data=data,
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    print(response.text)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["message"] == "Storage records created successfully."

    # now try submitting the CSV data with incorrect headers
    invalid_csv_content = (
        "device_id,flow_start,flow_end,flow_energy,validator_id\n"
        f"{fake_db_storage_device.id},2024-01-01T00:00:00Z,2024-01-01T01:00:00Z,-1000,0\n"
        f"{fake_db_storage_device.id},2024-01-01T01:00:00Z,2024-01-01T02:00:00Z,-1200,1\n"
        f"{fake_db_storage_device.id},2024-01-01T01:00:00Z,2024-01-01T03:00:00Z,1000,2\n"
        f"{fake_db_storage_device.id},2024-01-01T02:00:00Z,2024-01-01T04:00:00Z,-1500,3\n"
        f"{fake_db_storage_device.id},2024-01-01T03:00:00Z,2024-01-01T05:00:00Z,600,4\n"
    )

    invalid_records_csv_file = io.BytesIO(invalid_csv_content.encode("utf-8"))

    invalid_storage_files = {
        "file": ("invalid_records.csv", invalid_records_csv_file, "text/csv")
    }
    response = api_client.post(
        "/storage/storage_records",
        files=invalid_storage_files,
        data=data,
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    print(response.text)

    assert response.status_code == 400
    response_data = response.json()
    assert (
        "Measurement DataFrame is missing required columns."
        in response_data["error_message"]
    )


def test_submit_storage_records_invalid_timestamps(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_storage_device: Device,
    read_session: Session,
):
    """Test submission of storage records with invalid timestamps."""
    # Create a CSV string with invalid timestamps
    invalid_csv_content = (
        "device_id,flow_start_datetime,flow_end_datetime,flow_energy,validator_id\n"
        f"{fake_db_storage_device.id},invalid_date,2024-01-01T01:00:00Z,-1000,0\n"
        f"{fake_db_storage_device.id},2024-01-01T01:00:00Z,invalid_date,-1200,1\n"
    )

    records_csv_file = io.BytesIO(invalid_csv_content.encode("utf-8"))

    data = {
        "device_id": str(fake_db_storage_device.id),
    }

    storage_files = {"file": ("invalid_records.csv", records_csv_file, "text/csv")}

    response = api_client.post(
        "/storage/storage_records",
        files=storage_files,
        data=data,
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    print(response.text)

    assert response.status_code == 400
    response_data = response.json()
    assert "Error parsing datetime columns:" in response_data["error_message"]


def test_get_allocated_storage_records_by_device_id(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_storage_device: Device,
    fake_db_allocated_storage_records: list[AllocatedStorageRecord],
    read_session: Session,
):
    """Test retrieval of allocated storage records by device ID."""
    # Define the device ID to query
    device_id = fake_db_storage_device.id

    # Make the API request
    response = api_client.get(
        f"/storage/allocated_storage_records/{device_id}",
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    # Check the response status code
    assert response.status_code == 200

    # Check the response data structure
    response_data = response.json()
    assert isinstance(response_data, list)
    for record in response_data:
        assert "device_id" in record
        assert record["device_id"] == device_id


def test_get_allocated_storage_records_invalid_date_range_order(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_storage_device: Device,
    fake_db_allocated_storage_records: list[AllocatedStorageRecord],
):
    """Test 400 when created_after is not before created_before."""
    device_id = fake_db_storage_device.id
    created_after = datetime.datetime.now().date()
    created_before = (datetime.datetime.now() - datetime.timedelta(days=5)).date()

    response = api_client.get(
        f"/storage/allocated_storage_records/{device_id}",
        params={
            "created_after": created_after.isoformat(),
            "created_before": created_before.isoformat(),
        },
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    assert response.json() == {
        "status_code": 400,
        "error_message": "created_after must be before created_before.",
        "details": {},
        "error_type": "http_error",
    }


def test_get_allocated_storage_records_date_range_too_large(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_storage_device: Device,
    fake_db_allocated_storage_records: list[AllocatedStorageRecord],
):
    """Test 400 when date range exceeds 30 days."""
    device_id = fake_db_storage_device.id
    created_after = (datetime.datetime.now() - datetime.timedelta(days=35)).date()
    created_before = datetime.datetime.now().date()

    response = api_client.get(
        f"/storage/allocated_storage_records/{device_id}",
        params={
            "created_after": created_after.isoformat(),
            "created_before": created_before.isoformat(),
        },
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    assert response.json() == {
        "status_code": 400,
        "error_message": "Date range cannot exceed 30 days.",
        "details": {},
        "error_type": "http_error",
    }


@pytest.mark.parametrize(
    "unauthorized_role",
    [
        UserRoles.TRADING_USER,
        UserRoles.AUDIT_USER,
    ],
)
def test_unauthorized_user_role_access_denied(
    unauthorized_role: UserRoles,
    api_client: TestClient,
    account_factory,
    user_factory,
    auth_factory,
    fake_db_storage_device: Device,
    fake_db_allocated_storage_records: list[AllocatedStorageRecord],
):
    """Test that users without proper roles are denied access."""

    unauthorized_user = user_factory(unauthorized_role, "unauthorized")
    account = account_factory(unauthorized_user, "unauthorized_account")
    unauthorized_token = auth_factory(unauthorized_user)

    print("ACCOUNT", account.id, account.user_ids)
    print("UNAUTHORIZED USER", unauthorized_user.id, unauthorized_user.role)

    device_id = fake_db_storage_device.id

    response = api_client.get(
        f"/storage/allocated_storage_records/{device_id}",
        headers={"Authorization": f"Bearer {unauthorized_token}"},
    )

    print(response.text)
    assert response.status_code == 401
    assert response.json() == {
        "status_code": 401,
        "error_message": f"User does not have the required role: production_user, was: {unauthorized_role}",
        "details": {},
        "error_type": "http_error",
    }


def test_get_storage_records_by_id_success(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_storage_records: list[StorageRecord],
):
    """Test retrieval of storage records by ID."""
    storage_record_ids = [record.id for record in fake_db_storage_records]

    response = api_client.get(
        "/storage/storage_records",
        params={"storage_record_ids": storage_record_ids},
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == len(storage_record_ids)
    for record in response_data:
        assert record["id"] in storage_record_ids


def test_get_storage_records_by_id_invalid_ids(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_storage_records: list[StorageRecord],
):
    """Test retrieval of storage records by ID with invalid IDs."""
    invalid_ids = [500, 510, 520]

    response = api_client.get(
        "/storage/storage_records",
        params={"storage_record_ids": invalid_ids},
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert (
        "No storage records found for the specified IDs"
        in response_data["error_message"]
    )


def test_get_allocation_records_by_id_success(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_allocated_storage_records: list[AllocatedStorageRecord],
):
    """Test retrieval of allocation records by ID."""
    allocation_record_ids = [record.id for record in fake_db_allocated_storage_records]

    response = api_client.get(
        "/storage/allocated_storage_records_by_id",
        params={"allocated_storage_record_ids": allocation_record_ids},
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == len(allocation_record_ids)


def test_get_allocation_records_by_id_invalid_ids(
    api_client: TestClient,
    token_storage_validator: str,
    fake_db_allocated_storage_records: list[AllocatedStorageRecord],
):
    """Test retrieval of allocation records by ID with invalid IDs."""
    invalid_ids = [500, 510, 520]

    response = api_client.get(
        "/storage/allocated_storage_records_by_id",
        params={"allocated_storage_record_ids": invalid_ids},
        headers={"Authorization": f"Bearer {token_storage_validator}"},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert (
        "No allocated storage records found for the specified IDs"
        in response_data["error_message"]
    )
