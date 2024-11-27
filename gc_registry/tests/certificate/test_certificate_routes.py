
from esdbclient import EventStoreDBClient
from fastapi.testclient import TestClient
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.core.database.db import get_read_session, get_write_session
from gc_registry.main import app
from gc_registry.user.models import User

def test_transfer_certificate(
    api_client: TestClient,
    fake_db_gc_bundle: GranularCertificateBundle,
    fake_db_user: User,
    fake_db_account: Account,
    fake_db_account_2: Account,
    esdb_client: EventStoreDBClient,
):

    # Test case 1: Try to transfer a certificate without target_id
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
    }

    response = api_client.post("/certificate/transfer/", json=data)

    assert response.status_code == 422

    assert response.json()['detail'][0]['type'] == 'missing'
    assert 'target_id' in response.json()['detail'][0]['loc']

    # Test case 2: Try to transfer a certificate without source_id
    data.pop('source_id')
    data['target_id'] = fake_db_account_2.id

    response = api_client.post("/certificate/transfer/", json=data)

    assert response.json()['detail'][0]['type'] == 'missing'
    assert 'source_id' in response.json()['detail'][0]['loc']

    # Test case 3: Transfer a certificate successfully
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account_2.id
    }

    response = api_client.post("/certificate/transfer/", json=data)

    assert response.status_code == 202
    data = response.json()

    # Test case 4: Try to transfer a fraction of a certificate
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.75
    }

    response = api_client.post("/certificate/transfer/", json=data)

    assert response.status_code == 202
    data = response.json()

    # Test case 5: Try to transfer a certificate with invalid percentage
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account_2.id,
        "certificate_bundle_percentage": 1.5
    }

    response = api_client.post("/certificate/transfer/", json=data)

    assert response.status_code == 422

    assert response.json()['detail'][0]['type'] == 'less_than_equal'
    assert 'Input should be less than or equal to 1' in response.json()['detail'][0]['msg']

    # Test case 6: Try to specify the action type
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
        "target_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.5,
        "action_type": "cancel",
    }

    response = api_client.post("/certificate/transfer/", json=data)

    assert response.status_code == 422

    assert response.json()['detail'][0]['type'] == 'value_error'
    print(response.json())
    assert 'Value error, `action_type` cannot be set explicitly.' in response.json()['detail'][0]['msg']




def test_cancel_certificate(
    api_client,
    fake_db_gc_bundle: GranularCertificateBundle, 
    fake_db_user: User, 
    fake_db_account: Account,
    esdb_client: EventStoreDBClient
    ):
    # Test case 1: Try to cancel a certificate without source_id
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
    }

    response = api_client.post("/certificate/cancel/", json=data)

    assert response.status_code == 422

    assert response.json()['detail'][0]['type'] == 'missing'
    assert 'source_id' in response.json()['detail'][0]['loc']

    # Test case 2: Cancel a certificate successfully
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
    }

    response = api_client.post("/certificate/cancel/", json=data)

    assert response.status_code == 202

    # Test case 3: Try to cancel a fraction of a certificate
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
        "certificate_bundle_percentage": 0.35
    }

    response = api_client.post("/certificate/cancel/", json=data)

    assert response.status_code == 202


    # Test case 4: Try to cancel a certificate with invalid percentage
    data = {
        "granular_certificate_bundle_ids": [fake_db_gc_bundle.id],
        "user_id":fake_db_user.id,
        "source_id": fake_db_account.id,
        "certificate_bundle_percentage": 0
    }

    response = api_client.post("/certificate/cancel/", json=data)

    assert response.status_code == 422

    assert response.json()['detail'][0]['type'] == 'greater_than'
    assert 'Input should be greater than 0' in response.json()['detail'][0]['msg']
