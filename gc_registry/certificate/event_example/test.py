import datetime
from typing import Generator
import pytest

from sqlalchemy import Engine, create_engine, text
from sqlmodel import SQLModel, Session
from gc_registry.certificate.event_example.application import Registry
from gc_registry.certificate.models import GranularCertificateBundle


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """
    Creates an ephemeral Postgres database, creates base tables and exposes a scoped SQLModel Session.

    This fixture ensures the engine is disposed of and the container is stopped after all tests are done.
    """
    registry = Registry()
    env = registry.env
    connection_str = f"postgresql://{env['POSTGRES_USER']}:{env['POSTGRES_PASSWORD']}@{env['POSTGRES_HOST']}:{env['POSTGRES_PORT']}/{env['POSTGRES_DB']}"

    db_engine = create_engine(connection_str, pool_pre_ping=True)
    try:

        SQLModel.metadata.create_all(db_engine)

        yield db_engine
    finally:
        SQLModel.metadata.drop_all(db_engine)


@pytest.fixture(scope="function")
def db_session(db_engine: Engine) -> Generator[Session, None, None]:
    """
    Provides a SQLModel Session for tests, wrapped in a transaction.

    This ensures that any changes made to the database during a test are rolled back after the test completes,
    allowing tests to run in isolation and leaving the database in a clean state.

    See: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """

    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        # Ensure the session and transaction are properly closed/rolled back
        session.close()
        transaction.rollback()
        connection.close()


def clear_event_table(db_session):

    with db_session:
        # delete all data from registry_events
        query = text("DELETE FROM registry_events")
        db_session.exec(query)
        db_session.commit()


def test_registry(db_session):

    # Construct application object.
    registry = Registry()

    clear_event_table(db_session)

    with registry.recorder.transaction() as session:

        # Evolve application state.
        certificate_bundle_data = {
            "device_id": 1,
            "account_id": 1,
            "bundle_id_range_start": 1,
            "bundle_id_range_end": 10,
            "bundle_quantity": 10,
            "production_starting_interval": datetime.datetime(2024, 1, 1, 0, 0, 0),
            "production_ending_interval": datetime.datetime(2024, 1, 1, 0, 30, 0),
            "certificate_status": "Active",
            "face_value": 10,
            "energy_carrier": "wind",
            "energy_source": "wind",
            "issuance_post_energy_carrier_conversion": False,
            "issuance_datestamp": datetime.datetime(2024, 1, 1, 0, 0, 0),
            "expiry_datestamp": datetime.datetime(2026, 1, 1, 0, 30, 0),
            "is_storage": False,
        }
        gcb_id = registry.issue_certificate(**certificate_bundle_data)

        certificate_bundle_data.update({"id": gcb_id})

        orm_model = GranularCertificateBundle.model_validate(certificate_bundle_data)
        session.add(orm_model)

        # Query application state.
        gcb = registry.get_granular_certificate_bundle(gcb_id)
        assert gcb["device_id"] == 1
        assert gcb["face_value"] == certificate_bundle_data["face_value"]
        assert (
            gcb["certificate_status"] == certificate_bundle_data["certificate_status"]
        )

        transfer_account_id = 2
        registry.transfer(gcb_id, account_id=transfer_account_id)
        gcb = registry.get_granular_certificate_bundle(gcb_id)
        assert gcb["account_id"] == transfer_account_id

        registry.cancel(gcb_id)
        gcb = registry.get_granular_certificate_bundle(gcb_id)
        assert gcb["account_id"] == transfer_account_id
        assert gcb["certificate_status"] == "cancelled"

        # Select notifications.
        notifications = registry.notification_log.select(start=1, limit=10)
        assert len(notifications) == 3

        del registry

        registry = Registry()
        gcb = registry.get_granular_certificate_bundle(gcb_id)
        assert gcb["device_id"] == 1
        assert gcb["face_value"] == certificate_bundle_data["face_value"]
        assert gcb["certificate_status"] == "cancelled"

        notifications = registry.notification_log.select(start=1, limit=10)
        assert len(notifications) == 3
