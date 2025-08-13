import datetime
import io
import json
from functools import partial
from typing import Any, Hashable, Type, TypeVar

import pandas as pd
from esdbclient import EventStoreDBClient
from fastapi import HTTPException
from pydantic import BaseModel, model_validator
from sqlmodel import Field, Session, SQLModel, select

from gc_registry.core.database import cqrs

T = TypeVar("T", bound="ActiveRecord")

utc_datetime_now = partial(datetime.datetime.now, datetime.timezone.utc)


class ActiveRecord(SQLModel):
    created_at: datetime.datetime = Field(
        default_factory=utc_datetime_now, nullable=False
    )

    @classmethod
    def by_id(
        cls: Type[T],
        id_: int,
        session: Session,
        close_session: bool = False,
    ) -> T:
        obj = session.get(cls, id_)
        if obj is None:
            raise HTTPException(
                status_code=404, detail=f"{cls.__name__} with id {id_} not found"
            )
        if close_session:
            session.close()
        return obj

    @model_validator(mode="before")
    @classmethod
    def sanitise_nan_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for k, v in data.items():
            try:
                if pd.isna(v):
                    data[k] = None
            except (TypeError, ValueError):
                pass

        return data

    @classmethod
    def all(cls, session: Session) -> list[SQLModel]:
        return session.exec(select(cls)).all()

    @classmethod
    def exists(cls, id_: int, session: Session) -> bool:
        return session.get(cls, id_) is not None

    @classmethod
    def create(
        cls,
        source: list[dict[Hashable, Any]]
        | dict[Hashable, Any]
        | dict[str, Any]
        | BaseModel,
        write_session: Session,
        read_session: Session,
        esdb_client: EventStoreDBClient,
        **kwargs,
    ) -> list[SQLModel]:
        if isinstance(source, (SQLModel, BaseModel)):
            obj = [cls.model_validate(source)]
        elif isinstance(source, dict):
            obj = [cls.model_validate_json(json.dumps(source))]
        elif isinstance(source, list):
            obj = [cls.model_validate_json(json.dumps(elem)) for elem in source]
        else:
            raise ValueError(f"The input type {type(source)} can not be processed")

        # logger.debug(f"Creating {cls.__name__}: {obj[0].model_dump_json()}")
        created_entities = cqrs.write_to_database(
            obj,  # type: ignore
            write_session,
            read_session,
            esdb_client,
            **kwargs,
        )

        return created_entities

    def update(
        self,
        update_entity: BaseModel,
        write_session: Session,
        read_session: Session,
        esdb_client: EventStoreDBClient,
    ) -> SQLModel | None:
        # logger.debug(f"Updating {self.__class__.__name__}: {self.model_dump_json()}")
        updated_entity = cqrs.update_database_entity(
            entity=self,
            update_entity=update_entity,
            write_session=write_session,
            read_session=read_session,
            esdb_client=esdb_client,
        )

        return updated_entity

    def delete(
        self,
        write_session: Session,
        read_session: Session,
        esdb_client: EventStoreDBClient,
    ) -> list[SQLModel] | None:
        # logger.debug(f"Deleting {self.__class__.__name__}: {self.model_dump_json()}")
        deleted_entities = cqrs.delete_database_entities(
            entities=self,
            write_session=write_session,
            read_session=read_session,
            esdb_client=esdb_client,
        )

        return deleted_entities


def parse_import_file(filename: str | None, content: str) -> pd.DataFrame:
    """Parse the import file content into a pandas DataFrame.

    Supports both CSV and JSON formats.

    Args:
        filename (str | None): The original filename (used to determine file type)
        content (str): The file content as a string

    Returns:
        pd.DataFrame: Parsed data as a pandas DataFrame

    Raises:
        ValueError: If the file format is not supported or parsing fails
    """
    # Determine file type from filename extension
    file_type = None
    if filename:
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            file_type = "csv"
        elif filename_lower.endswith(".json"):
            file_type = "json"

    # If we can't determine from filename, try to parse as JSON first, then CSV
    if file_type is None:
        try:
            # Try parsing as JSON first
            json.loads(content)
            file_type = "json"
        except json.JSONDecodeError:
            # Fall back to CSV
            file_type = "csv"

    try:
        if file_type == "csv":
            # Parse CSV using existing logic
            csv_file = io.StringIO(content)
            return pd.read_csv(csv_file)

        elif file_type == "json":
            # Parse JSON
            json_data = json.loads(content)

            # Support array of objects format: [{"col1": "val1", "col2": "val2"}, ...]
            if isinstance(json_data, list):
                if not json_data:
                    raise ValueError("JSON file contains an empty array")

                # Ensure all items are dictionaries
                if not all(isinstance(item, dict) for item in json_data):
                    raise ValueError("JSON array must contain only objects")

                return pd.DataFrame(json_data)

            # Support object format with arrays: {"col1": ["val1", "val2"], "col2": ["val3", "val4"]}
            elif isinstance(json_data, dict):
                return pd.DataFrame(json_data)

            else:
                raise ValueError(
                    "JSON format not supported. Use array of objects or object with arrays format."
                )

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")
    except pd.errors.EmptyDataError:
        raise ValueError("The uploaded file is empty")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing CSV file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing file: {str(e)}")
