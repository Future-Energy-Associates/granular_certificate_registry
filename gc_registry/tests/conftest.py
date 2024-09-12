from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlmodel import Session, SQLModel
from testcontainers.postgres import PostgresContainer

from gc_registry.account.models import Account
from gc_registry.device.models import Device
from gc_registry.user.models import User


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """
    Creates ephemeral Postgres DB, creates base tables and exposes a scoped SQLModel Session
    """

    pg_container = PostgresContainer("postgres:15-alpine", driver="psycopg")
    pg_container.start()

    url = pg_container.get_connection_url()
    db_engine = create_engine(url)

    SQLModel.metadata.create_all(db_engine)

    yield db_engine

    db_engine.dispose()
    pg_container.stop()


@pytest.fixture(scope="function")
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """
    Returns a DB session wrapped in a transaction that rolls back all changes after each test
    See: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """

    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def fake_db_user(db_session) -> User:
    user_dict = {
        "name": "fake_user",
        "primary_contact": "jake_fake@fakecorp.com",
    }

    user = User.model_validate(user_dict)

    db_session.add(user)
    db_session.commit()

    return user


@pytest.fixture()
def fake_db_account(db_session) -> Account:
    account_dict = {
        "account_name": "fake_account",
        "account_type": "fake_account_type",
        "account_status": "active",
        "account_balance": 1000,
        "account_currency": "USD",
        "account_country": "USA",
        "account_state": "NY",
    }

    account = Account.model_validate(account_dict)

    db_session.add(account)
    db_session.commit()

    return account


@pytest.fixture()
def fake_db_wind_device(db_session, fake_db_account) -> Device:
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
    }

    wind_device = Device.model_validate(device_dict)

    db_session.add(wind_device)
    db_session.commit()

    return wind_device


@pytest.fixture()
def fake_db_solar_device(db_session, fake_db_account) -> Device:
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
    }

    solar_device = Device.model_validate(device_dict)

    db_session.add(solar_device)
    db_session.commit()

    return solar_device
