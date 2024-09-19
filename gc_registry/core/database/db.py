import importlib
from typing import Any, Generator

import numpy as np
from sqlalchemy_utils import create_database, database_exists  # type: ignore
from sqlmodel import Session, SQLModel, create_engine

from gc_registry.core.database.config import schema_paths_read, schema_paths_write
from gc_registry.settings import settings


# Defining utility functions and classes
def schema_path_to_class(schema_path):
    *module_path, schema_class_name = schema_path.split(".")
    schema_class = getattr(
        importlib.import_module(".".join(module_path)), schema_class_name
    )

    return schema_class


def df_to_records_without_nulls(df):
    records = [
        {k: v for k, v in record.items() if v is not None}
        for record in df.replace(np.nan, None).to_dict("records")
    ]

    return records


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
        with Session(self.engine) as session, session.begin():
            yield session

    def initiate_db_tables(self, schema_paths: list | None = None) -> None:
        if schema_paths is None:
            print("No schema paths provided. Skipping table creation.")
            schema_paths = []
        if not database_exists(self.engine.url):
            print("Database does not exist. Creating database...")
            create_database(self.engine.url)

        if len(schema_paths) > 0:
            print("Creating tables for the provided schema paths...")
            tables = [
                schema_path_to_class(schema_path).__table__
                for schema_path in schema_paths
            ]
        else:
            tables = None

        SQLModel.metadata.create_all(self.engine, tables=tables)

        return None


# Initialising the DButil clients

db_mapping = [
    ("db_read", settings.DATABASE_URL_READ, schema_paths_read),
    ("db_write", settings.DATABASE_URL_WRITE, schema_paths_write),
]

db_name_to_client = {}

print("Initialising the database clients....")
for db_name, db_url, schema_paths in db_mapping:
    db_client = DButils(
        db_url=db_url,
        db_name=db_name,
        db_username=settings.POSTGRES_USER,
        db_password=settings.POSTGRES_PASSWORD,
        db_port=settings.DATABASE_PORT,
        db_test_fp=settings.DB_TEST_FP,
        env=settings.ENVIRONMENT,
    )
    db_name_to_client[db_name] = db_client
    db_client.initiate_db_tables(schema_paths)
