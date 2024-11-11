import datetime
import json
import logging
from typing import Any, Type, TypeVar

from esdbclient import EventStoreDBClient
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from gc_registry.core.database import cqrs
from gc_registry.settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)


T = TypeVar("T", bound="ActiveRecord")


class ActiveRecord(SQLModel):
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow, nullable=False
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

    @classmethod
    def all(cls, session: Session) -> list[SQLModel]:
        return session.exec(select(cls)).all()

    @classmethod
    def exists(cls, id_: int, session: Session) -> bool:
        return session.get(cls, id_) is not None

    @classmethod
    def create(
        cls,
        source: dict[str, Any] | BaseModel,
        write_session: Session,
        read_session: Session,
        esdb_client: EventStoreDBClient,
    ) -> list[SQLModel] | None:
        if isinstance(source, (SQLModel, BaseModel)):
            obj = cls.model_validate(source)
        elif isinstance(source, dict):
            obj = cls.model_validate_json(json.dumps(source))
        else:
            raise ValueError(f"The input type {type(source)} can not be processed")

        logger.debug(f"Creating {cls.__name__}: {obj.model_dump_json()}")
        created_entities = cqrs.write_to_database(
            obj, write_session, read_session, esdb_client
        )

        return created_entities

    def save(self, session):
        session.add(self)
        session.commit()
        session.refresh(self)

    def update(
        self,
        update_entity: BaseModel,
        write_session: Session,
        read_session: Session,
        esdb_client: EventStoreDBClient,
    ) -> SQLModel | None:
        logger.debug(f"Updating {self.__class__.__name__}: {self.model_dump_json()}")
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
        logger.debug(f"Deleting {self.__class__.__name__}: {self.model_dump_json()}")
        deleted_entities = cqrs.delete_database_entities(
            entities=self,
            write_session=write_session,
            read_session=read_session,
            esdb_client=esdb_client,
        )

        return deleted_entities


def parse_nans_to_null(json_str: str, replace_nan: bool = True):
    if replace_nan:
        json_str = json_str.replace("nan", "null")
        json_str = json_str.replace("NaN", "null")
        json_str = json_str.replace("None", "null")
    else:
        pass

    return json_str


def sqlmodel_obj_to_json(sqlmodel_obj, response_model=None, replace_nan=True):
    if sqlmodel_obj is None:
        return None
    elif isinstance(sqlmodel_obj, list):
        json_content = [
            (
                json.loads(parse_nans_to_null(elem.json(), replace_nan))
                if response_model is None
                else json.loads(
                    parse_nans_to_null(
                        response_model.from_orm(elem).json(), replace_nan
                    )
                )
            )
            for elem in sqlmodel_obj
        ]
    elif response_model is not None:
        json_content = json.loads(
            parse_nans_to_null(
                response_model.from_orm(sqlmodel_obj).json(), replace_nan
            )
        )
    else:
        json_content = json.loads(parse_nans_to_null(sqlmodel_obj.json(), replace_nan))

    return json_content


def format_json_response(
    sqlmodel_obj,
    headers: dict | None = None,
    response_model=None,
    send_raw=False,
    pagination_metadata=None,
):
    if headers is None:
        headers = {}
    if send_raw:
        if pagination_metadata is not None:
            json_content = {
                "content": sqlmodel_obj,
                "pagination_metadata": pagination_metadata,
            }
        else:
            json_content = sqlmodel_obj

        return JSONResponse(content=json_content, headers=headers)

    if sqlmodel_obj is None:
        raise HTTPException(status_code=404, detail="Item not found")

    json_content = sqlmodel_obj_to_json(sqlmodel_obj, response_model=response_model)

    if pagination_metadata is not None:
        json_content = {
            "content": json_content,
            "pagination_metadata": pagination_metadata,
        }

    return JSONResponse(content=json_content, headers=headers)
