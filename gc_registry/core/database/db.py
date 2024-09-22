import importlib
from typing import Any, Generator

from sqlmodel import Session, SQLModel, create_engine

from gc_registry.account import models as account_models
from gc_registry.authentication import models as authentication_models
from gc_registry.certificate import models as certificate_models
from gc_registry.device import models as device_models
from gc_registry.measurement import models as measurement_models
from gc_registry.organisation import models as organisation_models
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
    "organisation_models",
    "account_models",
    "device_models",
    "certificate_models",
    "storage_models",
    "measurement_models",
]


# Defining utility functions and classes
def schema_path_to_class(schema_path):
    *module_path, schema_class_name = schema_path.split(".")
    schema_class = getattr(
        importlib.import_module(".".join(module_path)), schema_class_name
    )

    return schema_class


class DButils:
    def __init__(
        self,
        db_username: str | None = None,
        db_password: str | None = None,
        db_url: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        db_test_fp: str | None = None,
        env: str | None = "STAGE",
    ):
        self._db_username = db_username
        self._db_password = db_password
        self._db_url = db_url
        self._db_port = db_port
        self._db_name = db_name
        self._db_test_fp = db_test_fp

        if env == "PROD":
            self.connection_str = (
                f"postgresql://{self._db_username}:{self._db_password}@{self._db_url}:"
                f"{self._db_port}/{self._db_name}"
            )
        elif env == "STAGE":
            self.connection_str = f"sqlite:///{self._db_test_fp}"
        else:
            raise ValueError("`ENVIRONMENT` must be one of: `PROD` or `STAGE`")

        self.engine = create_engine(self.connection_str, pool_pre_ping=True)

    def yield_session(self) -> Generator[Any, Any, Any]:
        with Session(self.engine) as session:
            yield session


# Initialising the DButil clients
db_mapping = [
    ("read", settings.DATABASE_URL_READ),
    ("write", settings.DATABASE_URL_WRITE),
]

db_name_to_client = {}

for db_name, db_url in db_mapping:
    db_client = DButils(
        db_url=db_url,
        db_name=settings.POSTGRES_DB,
        db_username=settings.POSTGRES_USER,
        db_password=settings.POSTGRES_PASSWORD,
        db_port=settings.DATABASE_PORT,
        db_test_fp=settings.DB_TEST_FP,
        env=settings.ENVIRONMENT,
    )
    db_name_to_client[db_name] = db_client
