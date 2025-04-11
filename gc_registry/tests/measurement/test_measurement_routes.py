import io

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.certificate.models import GranularCertificateBundle, IssuanceMetaData
from gc_registry.device.models import Device


@pytest.fixture
def valid_measurement_csv():
    """Create a CSV string with valid measurement data."""
    return (
        "interval_usage,interval_start_datetime,interval_end_datetime,gross_net_indicator\n"
        "10,2024-11-18T10:00:00,2024-11-18T11:00:00,NET\n"
        "15,2024-11-18T11:00:00,2024-11-18T12:00:00,NET\n"
        "20,2024-11-18T12:00:00,2024-11-18T13:00:00,NET\n"
    )


def test_submit_readings_success(
    api_client: TestClient,
    token: str,
    valid_measurement_csv: str,
    fake_db_solar_device: Device,
    fake_db_issuance_metadata: IssuanceMetaData,
    read_session: Session,
):
    """Test successful submission of readings."""
    # Create file-like object from CSV string
    csv_file = io.BytesIO(valid_measurement_csv.encode("utf-8"))

    # Create files dict for multipart form data
    files = {"file": ("measurements.csv", csv_file, "text/csv")}

    # Create form data
    data = {
        "deviceID": str(fake_db_solar_device.id),  # Form data must be strings
    }

    response = api_client.post(
        "/measurement/submit_readings",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    response_data = response.json()
    assert response_data["message"] == "Readings submitted successfully."
    assert response_data["total_device_usage"] == 45
    assert response_data["first_reading_datetime"] == "2024-11-18T10:00:00Z"
    assert response_data["last_reading_datetime"] == "2024-11-18T12:00:00Z"

    # check that the certificates have been issued
    stmt: SelectOfScalar = select(GranularCertificateBundle).where(
        GranularCertificateBundle.device_id == fake_db_solar_device.id
    )
    certificates = read_session.exec(stmt).all()
    assert len(certificates) == 3
    assert sum(certificate.bundle_quantity for certificate in certificates) == 45
