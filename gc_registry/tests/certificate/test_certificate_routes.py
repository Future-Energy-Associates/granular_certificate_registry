from typing import Any

from esdbclient import EventStoreDBClient
from fastapi.testclient import TestClient
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.account.schemas import AccountUpdate
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.services import create_issuance_id
from gc_registry.user.models import User


def test_transfer_certificate(
    api_client: TestClient,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_user: User,
    fake_db_account: Account,
    fake_db_account_2: Account,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
):
    # Test case 1: Try to transfer a certificate without target_id
    test_data_1: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account.id,
    }

    response = api_client.post("/certificate/transfer", json=test_data_1)

    assert response.status_code == 422

    assert response.json()["detail"][0]["type"] == "missing"
    assert "target_id" in response.json()["detail"][0]["loc"]

    # Test case 2: Try to transfer a certificate without source_id
    test_data_1.pop("source_id")
    test_data_1["target_id"] = fake_db_account_2.id

    response = api_client.post("/certificate/transfer", json=test_data_1)

    assert response.json()["detail"][0]["type"] == "missing"
    assert "source_id" in response.json()["detail"][0]["loc"]

    # Test case 3: Transfer a certificate successfully

    # Whitelist the source account for the target account
    fake_db_account = write_session.merge(fake_db_account)
    fake_db_account.update(
        AccountUpdate(account_whitelist=[fake_db_account_2.id]),  # type: ignore
        write_session,
        read_session,
        esdb_client,
    )
    fake_db_account_2 = write_session.merge(fake_db_account_2)
    fake_db_account_2.update(
        AccountUpdate(account_whitelist=[fake_db_account.id]),  # type: ignore
        write_session,
        read_session,
        esdb_client,
    )

    test_data_2: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account_2.id,
    }

    response = api_client.post("/certificate/transfer", json=test_data_2)

    assert response.status_code == 202

    # Test case 4: Try to transfer a fraction of a certificate
    test_data_3: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account_2.id,
        "target_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.75,
    }

    response = api_client.post("/certificate/transfer", json=test_data_3)

    assert response.status_code == 202

    # Test case 5: Try to transfer a certificate with invalid percentage

    test_data_4: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account_2.id,
        "certificate_bundle_percentage": 1.5,
    }

    response = api_client.post("/certificate/transfer", json=test_data_4)

    assert response.status_code == 422

    assert response.json()["detail"][0]["type"] == "less_than_equal"
    assert (
        "Input should be less than or equal to 1" in response.json()["detail"][0]["msg"]
    )

    # Test case 6: Try to specify the action type
    test_data_5: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.5,
        "action_type": "cancel",
    }

    response = api_client.post("/certificate/transfer", json=test_data_5)

    assert response.status_code == 422

    assert response.json()["detail"][0]["type"] == "value_error"
    assert (
        "Value error, `action_type` cannot be set explicitly."
        in response.json()["detail"][0]["msg"]
    )


def test_cancel_certificate_no_source_id(
    api_client,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_user: User,
):
    # Test case 1: Try to cancel a certificate without source_id
    test_data_1: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
    }

    response = api_client.post("/certificate/cancel/", json=test_data_1)

    assert response.status_code == 422

    assert response.json()["detail"][0]["type"] == "missing"
    assert "source_id" in response.json()["detail"][0]["loc"]


def test_cancel_certificate_successfully(
    api_client: TestClient,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_user: User,
    fake_db_account: Account,
):
    # Test case 2: Cancel a certificate successfully
    test_data_2: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account.id,
    }

    response = api_client.post("/certificate/cancel/", json=test_data_2)

    assert response.status_code == 202


def test_cancel_certificate_fraction(
    api_client: TestClient,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_user: User,
    fake_db_account: Account,
):
    # Test case 3: Try to cancel a fraction of a certificate
    test_data_3: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.35,
    }

    response = api_client.post("/certificate/cancel/", json=test_data_3)

    assert response.status_code == 202

    # Test case 4: Try to cancel a certificate with invalid percentage
    test_data_4: dict[str, Any] = {
        "granular_certificate_bundle_ids": [fake_db_granular_certificate_bundle.id],
        "user_id": fake_db_user.id,
        "source_id": fake_db_account.id,
        "certificate_bundle_percentage": 0,
    }

    response = api_client.post("/certificate/cancel/", json=test_data_4)

    assert response.status_code == 422

    assert response.json()["detail"][0]["type"] == "greater_than"
    assert "Input should be greater than 0" in response.json()["detail"][0]["msg"]


def test_query_certificate_bundles(
    api_client,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_granular_certificate_bundle_2: GranularCertificateBundle,
    fake_db_user: User,
    fake_db_account: Account,
):
    assert fake_db_granular_certificate_bundle.id is not None
    assert fake_db_user.id is not None
    assert fake_db_account.id is not None

    # Test case 1: Try to query a certificate with correct parameters
    test_data_1: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
    }

    response = api_client.post("/certificate/query", json=test_data_1)

    assert response.status_code == 202
    assert "total_certificate_volume" in response.json().keys()
    assert (
        response.json()["total_certificate_volume"]
        == fake_db_granular_certificate_bundle.bundle_quantity
        + fake_db_granular_certificate_bundle_2.bundle_quantity
    )

    # Test case 2: Try to query a certificate with missing source_id
    test_data_2: dict[str, Any] = {
        "user_id": fake_db_user.id,
    }

    response = api_client.post("/certificate/query", json=test_data_2)

    assert response.status_code == 422

    assert response.json()["detail"][0]["type"] == "missing"
    assert "source_id" in response.json()["detail"][0]["loc"]

    # Test case 3: Query certificates based on issuance_ids
    test_data_3: dict[str, Any] = {
        "issuance_ids": [
            create_issuance_id(fake_db_granular_certificate_bundle),
            create_issuance_id(fake_db_granular_certificate_bundle_2),
        ],
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
    }

    response = api_client.post("/certificate/query", json=test_data_3)

    assert response.status_code == 202
    assert "total_certificate_volume" in response.json().keys()
    assert (
        response.json()["total_certificate_volume"]
        == fake_db_granular_certificate_bundle.bundle_quantity
        + fake_db_granular_certificate_bundle_2.bundle_quantity
    )
    assert (
        "id" in response.json()["granular_certificate_bundles"][0].keys()
    ), "ID not in returned data"

    # Test case 4: Query certificates with invalid issuance_ids

    test_data_4: dict[str, Any] = {
        "issuance_ids": ["123-12-03-01 12:12:12"],
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
    }

    response = api_client.post("/certificate/query", json=test_data_4)

    assert response.status_code == 422

    assert "Invalid issuance ID:" in response.json()["detail"]

    # Test case 5: Query certificates with invalid certificate_period_start and certificate_period_end
    test_data_5: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
        "certificate_period_start": "2024-01-01",
        "certificate_period_end": "2020-01-01",
    }

    response = api_client.post("/certificate/query", json=test_data_5)

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "certificate_period_end must be greater than certificate_period_start."
    )

    # Test case 6: Query certificates with invalid certificate_period_start and certificate_period_end > 30 days
    test_data_6: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
        "certificate_period_start": "2024-01-01",
        "certificate_period_end": "2024-05-01",
    }

    response = api_client.post("/certificate/query", json=test_data_6)

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Difference between certificate_period_start and certificate_period_end must be 30 days or less."
    )

    # Test case 7: Query certificates with issuance_ids and certificate_period_start and certificate_period_end
    test_data_7: dict[str, Any] = {
        "issuance_ids": [create_issuance_id(fake_db_granular_certificate_bundle)],
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
        "certificate_period_start": "2024-01-01",
        "certificate_period_end": "2024-01-02",
    }

    response = api_client.post("/certificate/query", json=test_data_7)

    assert response.status_code == 422

    assert (
        response.json()["detail"]
        == "Cannot provide issuance_ids with certificate_period_start or certificate_period_end."
    )

    # Test case 8: Query certificates with invalid certificate_period_start and certificate_period_end
    test_data_8: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
        "certificate_period_start": "a date string",
        "certificate_period_end": "another date string",
    }

    response = api_client.post("/certificate/query", json=test_data_8)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "datetime_from_date_parsing"
    assert (
        "Input should be a valid datetime or date"
        in response.json()["detail"][0]["msg"]
    )

    # Test case 9: Try giving period start more than 30 days in the past with no end date
    test_data_9: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
        "certificate_period_start": "2023-01-01",
    }

    response = api_client.post("/certificate/query", json=test_data_9)

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "certificate_period_end must be provided if certificate_period_start is more than 30 days ago."
    )

    # Test case 10: Try with period end, but no start date
    test_data_10: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
        "certificate_period_end": "2023-01-01",
    }

    response = api_client.post("/certificate/query", json=test_data_10)

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "certificate_period_start must be provided if certificate_period_end is provided."
    )

    # Test case 11: Try to query certificates with invalid energy_source
    test_data_11: dict[str, Any] = {
        "source_id": fake_db_account.id,
        "user_id": fake_db_user.id,
        "energy_source": "windy",
    }

    response = api_client.post("/certificate/query", json=test_data_11)

    assert response.status_code == 422

    print(response.json())
    assert response.json()["detail"][0]["type"] == "enum"
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be 'solar_pv', 'wind', 'hydro', 'biomass', 'nuclear', 'electrolysis', 'geothermal', 'battery_storage', 'chp' or 'other'"
    )
