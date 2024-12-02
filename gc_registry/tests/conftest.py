import os
from typing import Generator

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
)
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.models import Device
from gc_registry.logging_config import logger
from gc_registry.main import app
from gc_registry.settings import settings
from gc_registry.user.models import User
from gc_registry.utils import ActiveRecord

load_dotenv()


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
    assert read_entity.id == entity.id  # type: ignore

    # read_entity = read_session.merge(read_entity)
    read_session.add(read_entity)
    read_session.commit()
    read_session.refresh(read_entity)

    return read_entity


@pytest.fixture()
def fake_db_user(write_session: Session, read_session: Session) -> User:
    user_dict = {
        "name": "fake_user",
        "primary_contact": "jake_fake@fakecorp.com",
        "roles": ["admin"],
    }

    user_write = User.model_validate(user_dict)

    user_read = add_entity_to_write_and_read(user_write, write_session, read_session)

    return user_read


@pytest.fixture()
def fake_db_account(write_session: Session, read_session: Session) -> Account:
    account_dict = {
        "account_name": "fake_account",
        "user_ids": [],
        "roles": ["admin"],
    }
    account_write = Account.model_validate(account_dict)

    account_read = add_entity_to_write_and_read(
        account_write, write_session, read_session
    )

    return account_read


@pytest.fixture()
def fake_db_account_2(write_session: Session, read_session: Session) -> Account:
    account_dict = {
        "account_name": "fake_account_2",
        "user_ids": [],
        "roles": ["admin"],
    }
    account_write = Account.model_validate(account_dict)

    account_read = add_entity_to_write_and_read(
        account_write, write_session, read_session
    )

    return account_read


@pytest.fixture()
def fake_db_wind_device(
    write_session: Session, read_session: Session, fake_db_account: Account
) -> Device:
    device_dict = {
        "device_name": "fake_wind_device",
        "meter_data_id": "BMU-XYZ",
        "grid": "fake_grid",
        "energy_source": EnergySourceType.wind,
        "technology_type": DeviceTechnologyType.wind_turbine,
        "capacity": 3000,
        "account_id": fake_db_account.id,
        "fuel_source": "wind",
        "location": "USA",
        "commissioning_date": "2020-01-01",
        "operational_date": "2020-01-01",
        "peak_demand": 100,
        "is_storage": False,
        "is_deleted": False,
    }

    wind_device = Device.model_validate(device_dict)

    device_read = add_entity_to_write_and_read(wind_device, write_session, read_session)

    return device_read


@pytest.fixture()
def fake_db_solar_device(
    write_session: Session, read_session: Session, fake_db_account: Account
) -> Device:
    device_dict = {
        "device_name": "fake_solar_device",
        "grid": "fake_grid",
        "energy_source": EnergySourceType.solar_pv,
        "technology_type": DeviceTechnologyType.solar_pv,
        "meter_data_id": "BMU-ABC",
        "capacity": 1000,
        "account_id": fake_db_account.id,
        "fuel_source": "solar",
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
        "sdr_allocation_id": None,
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
        "sdr_allocation_id": None,
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
