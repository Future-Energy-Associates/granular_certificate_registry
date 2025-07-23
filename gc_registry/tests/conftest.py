import logging
import os
from typing import Any, Callable, Generator

import pytest
from dotenv import load_dotenv
from esdbclient import EventStoreDBClient, NewEvent, StreamState
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlmodel import Session, SQLModel
from starlette.testclient import TestClient
from testcontainers.core.container import DockerContainer  # type: ignore
from testcontainers.core.waiting_utils import wait_for_logs  # type: ignore
from testcontainers.postgres import PostgresContainer  # type: ignore

from gc_registry.account.models import Account
from gc_registry.authentication.services import get_password_hash
from gc_registry.certificate.models import (
    GranularCertificateBundle,
    IssuanceMetaData,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import (
    CertificateStatus,
    DeviceTechnologyType,
    EnergyCarrierType,
    EnergySourceType,
    UserRoles,
)
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.models import Device
from gc_registry.logging_config import logger
from gc_registry.main import app
from gc_registry.settings import settings
from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord
from gc_registry.user.models import User, UserAccountLink
from gc_registry.utils import ActiveRecord

load_dotenv()


def pytest_configure(config):
    logger = logging.getLogger("testcontainers")
    logger.disabled = True


@pytest.fixture()
def api_client(
    write_session: Session, read_session: Session, esdb_client: EventStoreDBClient
) -> Generator[TestClient, None, None]:
    """API Client for testing routes"""

    def get_write_session_override():
        assert write_session.is_active
        return write_session

    def get_read_session_override():
        assert read_session.is_active
        return read_session

    def get_db_name_to_client_override():
        return {
            "write": write_session,
            "read": read_session,
        }

    def get_esdb_client_override():
        return esdb_client

    # Set dependency overrides
    app.dependency_overrides[db.get_write_session] = get_write_session_override
    app.dependency_overrides[db.get_read_session] = get_read_session_override
    app.dependency_overrides[db.get_db_name_to_client] = get_db_name_to_client_override
    app.dependency_overrides[events.get_esdb_client] = get_esdb_client_override

    with TestClient(app) as client:
        response = client.get("/csrf-token")
        csrf_token = response.json()["csrf_token"]
        client.headers["X-CSRF-Token"] = csrf_token
        yield client


def get_db_url(target: str = "write") -> str | None:
    if os.environ["ENVIRONMENT"] == "CI":
        url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@db_{target}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"
        return url
    else:
        try:
            pg_container = PostgresContainer(
                "postgres:15-alpine", driver="psycopg", dbname=f"db_{target}"
            )
            pg_container.start()
            return pg_container.get_connection_url()
        except Exception as e:
            logger.error(f"Failed to start PostgreSQL container: {str(e)}")
            return None


def get_esdb_url() -> str | None:
    if settings.ENVIRONMENT == "CI":
        return f"esdb://{settings.ESDB_CONNECTION_STRING}:2113?tls=false"
    else:
        try:
            esdb_container = (
                DockerContainer(image="eventstore/eventstore:23.10.2-bookworm-slim")
                .with_exposed_ports(2113)
                .with_bind_ports(2113, 2113)
                .maybe_emulate_amd64()
                .with_env("EVENTSTORE_RUN_PROJECTIONS", "All")
                .with_env("EVENTSTORE_CLUSTER_SIZE", 1)
                .with_env("EVENTSTORE_START_STANDARD_PROJECTIONS", True)
                .with_env("EVENTSTORE_HTTP_PORT", 2113)
                .with_env("EVENTSTORE_INSECURE", True)
                .with_env("EVENTSTORE_ENABLE_ATOM_PUB_OVER_HTTP", True)
                .with_env("EVENTSTORE_TELEMETRY_OPTOUT", True)
                .with_env("DOTNET_EnableWriteXorExecute", 0)
                .with_env("EVENTSTORE_ADVERTISE_HOST_TO_CLIENT_AS", "localhost")
                .with_env("EVENTSTORE_ADVERTISE_NODE_PORT_TO_CLIENT_AS", 2113)
            )
            esdb_container.start()
            _delay = wait_for_logs(esdb_container, "Not waiting for conditions")
            return "esdb://localhost:2113?tls=false"

        except Exception as e:
            print(f"Failed to start EventStoreDB container: {str(e)}")
            return None


@pytest.fixture(scope="session")
def write_engine() -> Generator[Engine, None, None]:
    """
    Creates ephemeral Postgres DB, creates base tables and exposes a scoped SQLModel Session
    """
    url = get_db_url("write")
    if url is None:
        raise ValueError("No db url for write")

    db_engine = create_engine(url)

    SQLModel.metadata.create_all(db_engine)

    yield db_engine
    db_engine.dispose()


@pytest.fixture(scope="session")
def read_engine() -> Generator[Engine, None, None]:
    """
    Creates ephemeral Postgres DB, creates base tables and exposes a scoped SQLModel Session
    """
    url = get_db_url("read")
    if url is None:
        raise ValueError("No db url for read")

    db_engine = create_engine(url)

    SQLModel.metadata.create_all(db_engine)

    yield db_engine
    db_engine.dispose()


@pytest.fixture(scope="function")
def write_session(write_engine: Engine) -> Generator[Session, None, None]:
    """
    Returns a DB session wrapped in a transaction that rolls back all changes after each test
    See: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """

    connection = write_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def read_session(read_engine: Engine) -> Generator[Session, None, None]:
    """
    Returns a DB session wrapped in a transaction that rolls back all changes after each test
    See: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """

    connection = read_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def esdb_client() -> Generator[EventStoreDBClient, None, None]:
    """Returns an instance of the EventStoreDBClient that rolls back the event
    stream after each test.
    """
    uri = get_esdb_url()

    client = EventStoreDBClient(uri=uri)
    client.append_event(
        stream_name="events",
        event=NewEvent(type="init", data=b"test_data"),
        current_version=StreamState.NO_STREAM,
    )
    yield client
    client.delete_stream("events", current_version=StreamState.EXISTS)


def add_entity_to_write_and_read(
    entity: ActiveRecord, write_session: Session, read_session: Session
):
    # Write entities to database first using the write session
    write_session.add(entity)
    write_session.commit()

    write_session.refresh(entity)

    # check that the entity has an ID
    # assert entity.id is not None  # type: ignore

    read_entity = read_session.merge(entity)

    if hasattr(entity, "id"):
        assert read_entity.id == entity.id  # type: ignore

    # read_entity = read_session.merge(read_entity)
    read_session.add(read_entity)
    read_session.commit()
    read_session.refresh(read_entity)

    return read_entity


@pytest.fixture()
def user_factory(write_session: Session, read_session: Session) -> Any:
    """Factory function to create users with different roles."""

    def _create_user(
        role: UserRoles, name_suffix: str = "", email_prefix: str = "test_user"
    ) -> ActiveRecord:
        role_name = str(role)
        unique_suffix = f"_{name_suffix}" if name_suffix else f"_{role_name}"

        user_dict = {
            "name": f"fake_user{unique_suffix}",
            "email": f"{email_prefix}{unique_suffix}@fakecorp.com",
            "hashed_password": get_password_hash("password"),
            "role": role,
        }

        user_write = User.model_validate(user_dict)
        user_read = add_entity_to_write_and_read(
            user_write, write_session, read_session
        )

        return user_read

    return _create_user


@pytest.fixture()
def account_factory(write_session: Session, read_session: Session) -> Any:
    """Factory function to create accounts with a specific user."""

    def _create_account(user: User, name_suffix: str = "") -> ActiveRecord:
        account_dict = {
            "account_name": f"fake_account_{str(user.role)}{name_suffix}",
            "user_ids": [user.id],
            "users": [user],
        }
        account_write = Account.model_validate(account_dict)

        account_read = add_entity_to_write_and_read(
            account_write, write_session, read_session
        )

        user_account_link = UserAccountLink.model_validate(
            {"user_id": user.id, "account_id": account_read.id}
        )

        _ = add_entity_to_write_and_read(user_account_link, write_session, read_session)

        return account_read

    return _create_account


@pytest.fixture()
def auth_factory(api_client: TestClient) -> Callable[[User], str]:
    """Factory function to create authentication tokens for users."""

    def _create_token(user: User) -> str:
        response = api_client.post(
            "auth/login",
            data={
                "username": user.email,
                "password": "password",
            },
        )
        return response.json()["access_token"]

    return _create_token


@pytest.fixture()
def generic_import_account(write_session: Session, read_session: Session) -> Account:
    """Create the generic import account."""
    account_dict = {
        "account_name": "Import Account",
        "user_ids": [],
    }

    account_write = Account.model_validate(account_dict)

    account_read = add_entity_to_write_and_read(
        account_write, write_session, read_session
    )

    return account_read


@pytest.fixture()
def import_device_json(generic_import_account: Account) -> dict:
    """Create a device JSON string."""
    return {
        "account_id": generic_import_account.id,
        "device_name": "Import Device",
        "local_device_identifier": "GENERIC_IMPORT_DEVICE",
        "grid": "N/A",
        "energy_source": EnergySourceType.solar_pv,
        "technology_type": DeviceTechnologyType.solar_pv,
        "operational_date": "2020-01-01",
        "capacity": 500,
        "peak_demand": 10,
        "location": "USA",
        "is_storage": False,
        "is_deleted": False,
    }


@pytest.fixture()
def fake_db_admin_user(user_factory) -> User:
    """Create an admin user."""
    return user_factory(UserRoles.ADMIN, "admin")


@pytest.fixture()
def token(auth_factory, fake_db_admin_user: User) -> str:
    """Get authentication token for admin user."""
    return auth_factory(fake_db_admin_user)


@pytest.fixture()
def fake_storage_validator_user(user_factory) -> User:
    return user_factory(UserRoles.STORAGE_VALIDATOR, "storage_validator")


@pytest.fixture()
def token_storage_validator(auth_factory, fake_storage_validator_user: User) -> str:
    return auth_factory(fake_storage_validator_user)


@pytest.fixture()
def fake_db_account(account_factory: Any, fake_db_admin_user: User) -> Account:
    return account_factory(fake_db_admin_user)


@pytest.fixture()
def fake_db_account_2(
    write_session: Session, read_session: Session, fake_db_admin_user: User
) -> Account:
    account_dict = {
        "account_name": "fake_account_2",
        "user_ids": [fake_db_admin_user.id],
        "users": [fake_db_admin_user],
    }
    account_write = Account.model_validate(account_dict)

    account_read = add_entity_to_write_and_read(
        account_write, write_session, read_session
    )

    user_account_link = UserAccountLink.model_validate(
        {"user_id": fake_db_admin_user.id, "account_id": account_read.id}
    )

    _ = add_entity_to_write_and_read(user_account_link, write_session, read_session)

    return account_read


@pytest.fixture()
def fake_db_account_storage_validator(
    write_session: Session, read_session: Session, fake_storage_validator_user: User
) -> Account:
    account_dict = {
        "account_name": "fake_account_storage_validator",
        "user_ids": [fake_storage_validator_user.id],
        "users": [fake_storage_validator_user],
    }

    account_write = Account.model_validate(account_dict)

    account_read = add_entity_to_write_and_read(
        account_write, write_session, read_session
    )

    user_account_link = UserAccountLink.model_validate(
        {"user_id": fake_storage_validator_user.id, "account_id": account_read.id}
    )

    _ = add_entity_to_write_and_read(user_account_link, write_session, read_session)

    return account_read


@pytest.fixture()
def device_factory(write_session: Session, read_session: Session) -> Any:
    """Factory function to create authentication tokens for users."""

    def _create_device(account: Account, device_kwargs: dict[str, Any] | None) -> Any:
        device_dict = {
            "grid": "fake_grid",
            "account_id": account.id,
            "location": "USA",
            "operational_date": "2020-01-01",
            "is_deleted": False,
        }
        if device_kwargs:
            device_dict.update(device_kwargs)

        device = Device.model_validate(device_dict)

        device_read = add_entity_to_write_and_read(device, write_session, read_session)

        return device_read

    return _create_device


@pytest.fixture()
def fake_db_wind_device(device_factory: Any, fake_db_account: Account) -> Device:
    device_dict = {
        "device_name": "fake_wind_device",
        "local_device_identifier": "BMU-XYZ",
        "energy_source": EnergySourceType.wind,
        "technology_type": DeviceTechnologyType.wind_turbine,
        "capacity": 3000,
        "peak_demand": 100,
        "is_storage": False,
    }
    return device_factory(fake_db_account, device_dict)


@pytest.fixture()
def fake_db_solar_device(
    write_session: Session, read_session: Session, fake_db_account: Account
) -> Device:
    device_dict = {
        "device_name": "fake_solar_device",
        "grid": "fake_grid",
        "energy_source": EnergySourceType.solar_pv,
        "technology_type": DeviceTechnologyType.solar_pv,
        "local_device_identifier": "BMU-ABC",
        "capacity": 1000,
        "account_id": fake_db_account.id,
        "location": "USA",
        "commissioning_date": "2020-01-01",
        "operational_date": "2020-01-01",
        "peak_demand": 100,
        "is_storage": False,
        "is_deleted": False,
    }

    solar_device = Device.model_validate(device_dict)

    device_read = add_entity_to_write_and_read(
        solar_device, write_session, read_session
    )

    return device_read


@pytest.fixture()
def fake_db_storage_device(
    write_session: Session,
    read_session: Session,
    fake_db_account_storage_validator: Account,
) -> Device:
    device_dict = {
        "device_name": "fake_storage_device",
        "grid": "fake_grid",
        "energy_source": EnergySourceType.battery_storage,
        "technology_type": DeviceTechnologyType.battery_storage,
        "local_device_identifier": "BMU-ST-XYZ",
        "capacity": 1000,
        "account_id": fake_db_account_storage_validator.id,
        "location": "USA",
        "commissioning_date": "2020-01-01",
        "operational_date": "2020-01-01",
        "peak_demand": 100,
        "is_storage": True,
        "is_deleted": False,
    }

    storage_device = Device.model_validate(device_dict)

    device_read = add_entity_to_write_and_read(
        storage_device, write_session, read_session
    )

    return device_read


@pytest.fixture()
def fake_db_issuance_metadata(
    write_session: Session, read_session: Session
) -> IssuanceMetaData:
    fake_db_issuance_metadata = {
        "country_of_issuance": "USA",
        "connected_grid_identification": "ERCOT",
        "issuing_body": "ERCOT",
        "legal_status": "legal",
        "issuance_purpose": "compliance",
        "support_received": None,
        "quality_scheme_reference": None,
        "dissemination_level": None,
        "issue_market_zone": "ERCOT",
    }

    issuance_metadata = IssuanceMetaData.model_validate(fake_db_issuance_metadata)
    issuance_metadata_read = add_entity_to_write_and_read(
        issuance_metadata, write_session, read_session
    )

    return issuance_metadata_read


@pytest.fixture()
def fake_db_granular_certificate_bundle(
    write_session: Session,
    read_session: Session,
    fake_db_account: Account,
    fake_db_wind_device: Device,
    fake_db_issuance_metadata: IssuanceMetaData,
) -> GranularCertificateBundle:
    granular_certificate_bundle_dict = {
        "account_id": fake_db_account.id,
        "certificate_bundle_status": CertificateStatus.ACTIVE,
        "metadata_id": fake_db_issuance_metadata.id,
        "certificate_bundle_id_range_start": 0,
        "certificate_bundle_id_range_end": 999,
        "bundle_quantity": 1000,
        "energy_carrier": EnergyCarrierType.electricity,
        "energy_source": EnergySourceType.wind,
        "face_value": 1,
        "is_storage": False,
        "allocated_storage_record_id": None,
        "storage_efficiency_factor": None,
        "issuance_post_energy_carrier_conversion": False,
        "device_id": fake_db_wind_device.id,
        "production_starting_interval": "2021-01-01T00:00:00",
        "production_ending_interval": "2021-01-01T01:00:00",
        "issuance_datestamp": "2021-01-01",
        "expiry_datestamp": "2024-01-01",
        "country_of_issuance": "USA",
        "connected_grid_identification": "ERCOT",
        "issuing_body": "ERCOT",
        "issue_market_zone": "USA",
        "emissions_factor_production_device": 0.0,
        "emissions_factor_source": "Some Data Source",
        "hash": "Some Hash",
    }

    granular_certificate_bundle_dict["issuance_id"] = (
        f"{granular_certificate_bundle_dict['device_id']}-{granular_certificate_bundle_dict['production_starting_interval']}"
    )

    granular_certificate_bundle = GranularCertificateBundle.model_validate(
        granular_certificate_bundle_dict
    )

    granular_certificate_bundle.hash = create_bundle_hash(granular_certificate_bundle)

    granular_certificate_bundle_read = add_entity_to_write_and_read(
        granular_certificate_bundle, write_session, read_session
    )

    # we actually want the bundle associated with the write session for these tests
    granular_certificate_bundle_write = write_session.merge(
        granular_certificate_bundle_read
    )

    return granular_certificate_bundle_write


@pytest.fixture()
def fake_db_granular_certificate_bundle_2(
    write_session: Session,
    read_session: Session,
    fake_db_account: Account,
    fake_db_solar_device: Device,
    fake_db_issuance_metadata: IssuanceMetaData,
) -> GranularCertificateBundle:
    granular_certificate_bundle_dict = {
        "account_id": fake_db_account.id,
        "certificate_bundle_status": CertificateStatus.ACTIVE,
        "metadata_id": fake_db_issuance_metadata.id,
        "certificate_bundle_id_range_start": 0,
        "certificate_bundle_id_range_end": 499,
        "bundle_quantity": 500,
        "energy_carrier": EnergyCarrierType.electricity,
        "energy_source": EnergySourceType.solar_pv,
        "face_value": 1,
        "is_storage": False,
        "allocated_storage_record_id": None,
        "storage_efficiency_factor": None,
        "issuance_post_energy_carrier_conversion": False,
        "device_id": fake_db_solar_device.id,
        "production_starting_interval": "2021-01-01T12:00:00",
        "production_ending_interval": "2021-01-01T13:00:00",
        "issuance_datestamp": "2021-01-01",
        "expiry_datestamp": "2024-01-01",
        "country_of_issuance": "USA",
        "connected_grid_identification": "ERCOT",
        "issuing_body": "ERCOT",
        "issue_market_zone": "USA",
        "emissions_factor_production_device": 0.0,
        "emissions_factor_source": "Some Data Source",
        "hash": "Some Hash",
    }

    granular_certificate_bundle_dict["issuance_id"] = (
        f"{granular_certificate_bundle_dict['device_id']}-{granular_certificate_bundle_dict['production_starting_interval']}"
    )

    granular_certificate_bundle = GranularCertificateBundle.model_validate(
        granular_certificate_bundle_dict
    )

    granular_certificate_bundle.hash = create_bundle_hash(granular_certificate_bundle)

    granular_certificate_bundle_read = add_entity_to_write_and_read(
        granular_certificate_bundle, write_session, read_session
    )

    # we actually want the bundle associated with the write session for these tests
    granular_certificate_bundle_write = write_session.merge(
        granular_certificate_bundle_read
    )

    return granular_certificate_bundle_write


@pytest.fixture
def valid_storage_record_csv():
    """Create a CSV string with valid storage record data."""
    return (
        "flow_start_datetime,flow_end_datetime,flow_energy,validator_id\n"
        "2024-01-01T00:00:00Z,2024-01-01T02:00:00Z,-1000,0\n"
        "2024-01-01T01:00:00Z,2024-01-01T03:00:00Z,-1200,1\n"
        "2024-01-01T02:00:00Z,2024-01-01T04:00:00Z,1000,2\n"
        "2024-01-01T03:00:00Z,2024-01-01T05:00:00Z,-1500,3\n"
        "2024-01-01T04:00:00Z,2024-01-01T06:00:00Z,600,4\n"
    )


@pytest.fixture
def valid_allocation_record_csv():
    """Create a CSV string with valid allocation record data."""
    return (
        "scr_allocation_id,sdr_allocation_id,sdr_proportion,scr_allocation_methodology,gc_allocation_id,sdgc_allocation_id,efficiency_factor_methodology,efficiency_factor_interval_start,efficiency_factor_interval_end,storage_efficiency_factor\n"
        "0,2,1.0,FIFO,,,EnergyTag Standard,2024-01-01 00:00:00,2025-01-01 00:00:00,0.87\n"
        "1,4,0.5,FIFO,,,EnergyTag Standard,2024-01-01 00:00:00,2025-01-01 00:00:00,0.87\n"
    )


@pytest.fixture()
def fake_db_storage_records(
    write_session: Session,
    read_session: Session,
    fake_db_storage_device: Device,
) -> list[StorageRecord]:
    """Create fake storage records for testing."""
    from gc_registry.storage.models import StorageRecord

    storage_record_dicts = [
        {
            "device_id": fake_db_storage_device.id,
            "is_charging": True,
            "flow_start_datetime": "2024-01-01T00:00:00",
            "flow_end_datetime": "2024-01-01T01:00:00",
            "flow_energy": 1000.0,
            "validator_id": 1,
            "is_deleted": False,
        },
        {
            "device_id": fake_db_storage_device.id,
            "is_charging": True,
            "flow_start_datetime": "2024-01-01T01:00:00",
            "flow_end_datetime": "2024-01-01T02:00:00",
            "flow_energy": 850.0,
            "validator_id": 1,
            "is_deleted": False,
        },
        {
            "device_id": fake_db_storage_device.id,
            "is_charging": True,
            "flow_start_datetime": "2024-01-01T02:00:00",
            "flow_end_datetime": "2024-01-01T03:00:00",
            "flow_energy": 1200.0,
            "validator_id": 1,
            "is_deleted": False,
        },
        {
            "device_id": fake_db_storage_device.id,
            "is_charging": True,
            "flow_start_datetime": "2024-01-01T03:00:00",
            "flow_end_datetime": "2024-01-01T04:00:00",
            "flow_energy": 1044.0,
            "validator_id": 1,
            "is_deleted": False,
        },
    ]

    db_storage_records = []
    for record_dict in storage_record_dicts:
        storage_record = StorageRecord.model_validate(record_dict)
        storage_record_read = add_entity_to_write_and_read(
            storage_record, write_session, read_session
        )
        db_storage_records.append(storage_record_read)

    return db_storage_records


@pytest.fixture
def fake_db_allocated_storage_records(
    write_session: Session,
    read_session: Session,
    fake_db_storage_device: Device,
    fake_db_granular_certificate_bundle: GranularCertificateBundle,
    fake_db_storage_records: list[StorageRecord],
) -> list[AllocatedStorageRecord]:
    allocation_dicts = [
        {
            "device_id": fake_db_storage_device.id,
            "granular_certificate_bundle_id": fake_db_granular_certificate_bundle.id,
            "storage_efficiency_factor": 0.87,
            "is_deleted": False,
            "scr_allocation_id": fake_db_storage_records[0].id,
            "sdr_allocation_id": fake_db_storage_records[1].id,
            "sdr_proportion": 0.5,
            "scr_allocation_methodology": "proportional",
            "gc_allocation_id": fake_db_granular_certificate_bundle.id,
            "sdgc_allocation_id": None,
            "efficiency_factor_methodology": "measured",
            "efficiency_factor_interval_start": "2024-01-01T00:00:00",
            "efficiency_factor_interval_end": "2025-01-01T00:00:00",
        },
        {
            "device_id": fake_db_storage_device.id,
            "granular_certificate_bundle_id": fake_db_granular_certificate_bundle.id,
            "storage_efficiency_factor": 0.87,
            "is_deleted": False,
            "scr_allocation_id": fake_db_storage_records[2].id,
            "sdr_allocation_id": fake_db_storage_records[3].id,
            "sdr_proportion": 0.3,
            "scr_allocation_methodology": "proportional",
            "gc_allocation_id": fake_db_granular_certificate_bundle.id,
            "sdgc_allocation_id": None,
            "efficiency_factor_methodology": "measured",
            "efficiency_factor_interval_start": "2024-01-01T00:00:00",
            "efficiency_factor_interval_end": "2025-01-01T00:00:00",
        },
    ]

    db_storage_allocation_records = []
    for allocation_dict in allocation_dicts:
        allocation = AllocatedStorageRecord.model_validate(allocation_dict)

        allocation_read = add_entity_to_write_and_read(
            allocation, write_session, read_session
        )
        db_storage_allocation_records.append(allocation_read)

    return db_storage_allocation_records
