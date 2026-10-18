from typing import Any, Generator
from urllib.parse import quote

from sqlmodel import Session, SQLModel, create_engine

from gc_registry.account import models as account_models
from gc_registry.authentication import models as authentication_models
from gc_registry.certificate import models as certificate_models
from gc_registry.device import models as device_models
from gc_registry.measurement import models as measurement_models
from gc_registry.settings import settings
from gc_registry.storage import models as storage_models
from gc_registry.user import models as user_models

"""
This section is used by Alembic to load the all the database related models
"""

__all__ = [
    "SQLModel",
    "user_models",
    "authentication_models",
    "account_models",
    "device_models",
    "certificate_models",
    "storage_models",
    "measurement_models",
]


def _quote_userinfo(value: str | None) -> str:
    """Percent-encode a URL user or password.

    Args:
        value: Raw credential. None is treated as empty.

    Returns:
        The encoded credential, safe to place in a PostgreSQL URL.
    """
    return quote(value or "", safe="")


def build_postgres_connection_url(
    username: str | None,
    password: str | None,
    host: str | None,
    port: int | None,
    database: str | None,
    gcp_instance: str | None,
) -> str:
    """Build a PostgreSQL URL for either Cloud SQL or a TCP host.

    A non-empty Cloud SQL instance name selects the unix socket URL. Any
    other instance name, including an empty string, selects TCP.

    Args:
        username: Database user.
        password: Database password.
        host: TCP hostname.
        port: TCP port.
        database: Database name.
        gcp_instance: Cloud SQL connection name, or empty when unused.

    Returns:
        A SQLAlchemy PostgreSQL connection URL.
    """
    user = _quote_userinfo(username)
    secret = _quote_userinfo(password)
    instance = (gcp_instance or "").strip()
    if instance:
        socket_path = f"/cloudsql/{instance}"
        return f"postgresql://{user}:{secret}@/{database}?host={socket_path}"

    return f"postgresql://{user}:{secret}@{host}:{port}/{database}"


class DButils:
    def __init__(
        self,
        db_username: str | None = None,
        db_password: str | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        gcp_instance: str | None = None,
        db_test_fp: str = "gc_registry_test.db",
        test: bool = False,
    ):
        self._db_username = db_username
        self._db_password = db_password
        self._db_host = db_host
        self._db_port = db_port
        self._db_name = db_name
        self._db_test_fp = db_test_fp
        self._gcp_instance = gcp_instance

        if test:
            self.connection_str = f"sqlite:///{self._db_test_fp}"
        else:
            self.connection_str = build_postgres_connection_url(
                username=self._db_username,
                password=self._db_password,
                host=self._db_host,
                port=self._db_port,
                database=self._db_name,
                gcp_instance=self._gcp_instance,
            )

        self.engine = create_engine(
            self.connection_str,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False,
        )

    def yield_session(self) -> Generator[Any, Any, Any]:
        with Session(self.engine) as session, session.begin():
            yield session

    def yield_twophase_session(self, write_object) -> Generator[Any, Any, Any]:
        with Session(self.engine, twophase=True) as session:
            yield session

    def get_session(self) -> Session:
        return Session(self.engine)


# Initialising the DButil clients
db_name_to_client: dict[str, Any] = {}


def get_db_name_to_client() -> dict[str, Any]:
    global db_name_to_client

    if db_name_to_client == {}:
        db_mapping = [
            ("db_read", settings.DATABASE_HOST_READ, settings.GCP_INSTANCE_READ),
            ("db_write", settings.DATABASE_HOST_WRITE, settings.GCP_INSTANCE_WRITE),
        ]

        for db_name, db_host, gcp_instance in db_mapping:
            db_client = DButils(
                db_host=db_host,
                db_name=settings.POSTGRES_DB,
                db_username=settings.POSTGRES_USER,
                db_password=settings.POSTGRES_PASSWORD,
                db_port=settings.DATABASE_PORT,
                gcp_instance=gcp_instance,
            )
            db_name_to_client[db_name] = db_client

    return db_name_to_client


def get_session(target: str) -> Generator[Session, None, None]:
    with next(db_name_to_client[target].yield_session()) as session:
        try:
            yield session
        finally:
            session.close()


def get_write_session() -> Session:
    return next(get_session("db_write"))


def get_read_session() -> Session:
    return next(get_session("db_read"))
