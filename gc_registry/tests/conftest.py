import logging
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from esdbclient import EventStoreDBClient, NewEvent, StreamState
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlmodel import Session, SQLModel
from starlette.testclient import TestClient
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.postgres import PostgresContainer

from gc_registry.account.models import Account
from gc_registry.core.database import db, events
from gc_registry.device.models import Device
from gc_registry.main import app
from gc_registry.settings import settings
from gc_registry.user.models import User

load_dotenv()


@pytest.fixture()
def api_client(
    db_write_session: Session, db_read_session: Session, esdb_client: EventStoreDBClient
) -> Generator[TestClient, None, None]:
    """API Client for testing routes"""

    def get_write_session_override():
        return db_write_session

    def get_read_session_override():
        return db_read_session

    def get_db_name_to_client_override():
        return {
            "write": db_write_session,
            "read": db_read_session,
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
        url = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@db_{target}/{settings.POSTGRES_DB}"
        return url
    else:
        try:
            pg_container = PostgresContainer(
                "postgres:15-alpine", driver="psycopg", dbname=f"db_{target}"
            )
            pg_container.start()
            return pg_container.get_connection_url()
        except Exception as e:
            logging.error(f"Failed to start PostgreSQL container: {str(e)}")
            return None


def get_esdb_url() -> str | None:
    if os.environ["ENVIRONMENT"] == "CI":
        return f"esdb://{os.environ['ESDB_CONNECTION_STRING']}:2113?tls=false"
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
            connection_string = (
                "esdb://"
                + esdb_container.get_docker_client().gateway_ip(
                    esdb_container._container.id
                )
                + ":2113?tls=false"
            )
            print("Connection string: ", connection_string)
            # return connection_string
            return "esdb://localhost:2113?tls=false"

        except Exception as e:
            print(f"Failed to start EventStoreDB container: {str(e)}")
            return None


@pytest.fixture(scope="session")
def db_write_engine() -> Generator[Engine, None, None]:
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
def db_read_engine() -> Generator[Engine, None, None]:
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
def db_write_session(db_write_engine: Engine) -> Generator[Session, None, None]:
    """
    Returns a DB session wrapped in a transaction that rolls back all changes after each test
    See: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """

    connection = db_write_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def db_read_session(db_read_engine: Engine) -> Generator[Session, None, None]:
    """
    Returns a DB session wrapped in a transaction that rolls back all changes after each test
    See: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """

    connection = db_read_engine.connect()
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


@pytest.fixture()
def fake_db_user(db_write_session: Session, db_read_session: Session) -> User:
    user_dict = {
        "name": "fake_user",
        "primary_contact": "jake_fake@fakecorp.com",
        "roles": ["admin"],
    }

    user_write = User.model_validate(user_dict)
    user_read = User.model_validate(user_dict)

    db_write_session.add(user_write)
    db_write_session.commit()

    db_read_session.add(user_read)
    db_read_session.commit()

    return user_write


@pytest.fixture()
def fake_db_account(db_write_session: Session, db_read_session: Session) -> Account:
    account_dict = {
        "account_name": "fake_account",
        "account_type": "fake_account_type",
        "account_status": "active",
        "account_balance": 1000,
        "account_currency": "USD",
        "account_country": "USA",
        "account_state": "NY",
    }

    account_write = Account.model_validate(account_dict)
    account_read = Account.model_validate(account_dict)

    db_write_session.add(account_write)
    db_write_session.commit()

    db_read_session.add(account_read)
    db_read_session.commit()

    return account_write


@pytest.fixture()
def fake_db_wind_device(db_write_session, fake_db_account) -> Device:
    device_dict = {
        "device_name": "fake_wind_device",
        "grid": "fake_grid",
        "energy_source": "wind",
        "technology_type": "wind",
        "capacity": 3000,
        "account_id": fake_db_account.id,
        "device_type": "wind",
        "is_renewable": True,
        "fuel_source": "wind",
        "location": "USA",
        "capacity_mw": 100,
        "commissioning_date": "2020-01-01",
        "operational_date": "2020-01-01",
        "peak_demand": 100,
        "is_deleted": False,
    }

    wind_device = Device.model_validate(device_dict)

    db_write_session.add(wind_device)
    db_write_session.commit()

    return wind_device


@pytest.fixture()
def fake_db_solar_device(db_write_session, fake_db_account) -> Device:
    device_dict = {
        "device_name": "fake_solar_device",
        "grid": "fake_grid",
        "energy_source": "solar",
        "technology_type": "solar",
        "capacity": 1000,
        "account_id": fake_db_account.id,
        "device_type": "solar",
        "is_renewable": True,
        "fuel_source": "solar",
        "location": "USA",
        "capacity_mw": 100,
        "commissioning_date": "2020-01-01",
        "operational_date": "2020-01-01",
        "peak_demand": 100,
        "is_deleted": False,
    }

    solar_device = Device.model_validate(device_dict)

    db_write_session.add(solar_device)
    db_write_session.commit()

    return solar_device
