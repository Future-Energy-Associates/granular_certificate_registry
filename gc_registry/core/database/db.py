from typing import Any, Generator

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


class DButils:
    def __init__(
        self,
        db_username: str | None = None,
        db_password: str | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        db_test_fp: str = "gc_registry_test.db",
        test: bool = False,
    ):
        self._db_username = db_username
        self._db_password = db_password
        self._db_host = db_host
        self._db_port = db_port
        self._db_name = db_name
        self._db_test_fp = db_test_fp

        if test:
            self.connection_str = f"sqlite:///{self._db_test_fp}"
        else:
            self.connection_str = f"postgresql://{self._db_username}:{self._db_password}@{self._db_host}:{self._db_port}/{self._db_name}"

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


# Initialising the DButil clients
db_name_to_client: dict[str, Any] = {}


def get_db_name_to_client():
    global db_name_to_client

    if db_name_to_client == {}:
        db_mapping = [
            ("db_read", settings.DATABASE_HOST_READ),
            ("db_write", settings.DATABASE_HOST_WRITE),
        ]

        for db_name, db_host in db_mapping:
            db_client = DButils(
                db_host=db_host,
                db_name=settings.POSTGRES_DB,
                db_username=settings.POSTGRES_USER,
                db_password=settings.POSTGRES_PASSWORD,
                db_port=settings.DATABASE_PORT,
            )
            db_name_to_client[db_name] = db_client

    return db_name_to_client


def get_write_session() -> Generator[Session, None, None]:
    db_client = db_name_to_client["db_write"]
    yield next(db_client.yield_session())

def get_read_session() -> Generator[Session, None, None]:
    db_client = db_name_to_client["db_read"]
    yield next(db_client.yield_session())
