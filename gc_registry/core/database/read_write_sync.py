from datetime import datetime
from enum import Enum

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import JSON, Column, DateTime, Integer, String, func
from sqlmodel import Field, SQLModel

from gc_registry.core.database.db import db_name_to_client

router = APIRouter(tags=["Sync"])


class EventTypes(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class Event(SQLModel, table=True):
    __tablename__ = "events"
    id: int = Field(primary_key=True)
    entity_id: int
    entity_name: str
    event_type: EventTypes
    attributes_before: dict | None = Field(sa_column=Column(JSON))
    attributes_after: dict | None = Field(sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


def transform_write_entities_to_read(entities):
    return entities


def write_to_database(entities):
    # Create a list of Event entries for this operation
    events = [
        Event(
            entity_id=entity.id,
            entity_name=entity.__class__.__name__,
            event_type=EventTypes.CREATE,
        )
        for entity in entities
    ]

    with db_name_to_client["write"].yield_session() as write_session:
        try:
            # Batch write the entities to the write database first
            write_session.add_all(entities)
            write_session.add_all(events)

        except Exception as e:
            print(f"Error during write: {str(e)}")
            write_session.rollback()

    # if needed, transform the entity into its equivalent read DB representation
    read_entities = transform_write_entities_to_read(entities)

    # Write the entity to the read database
    with db_name_to_client["read"].yield_session() as read_session:
        try:
            read_session.add_all(read_entities)
        except Exception as e:
            print(f"Error during read: {str(e)}")
            read_session.rollback()

    return


def update_database_entity(entity):
    # Create an Event entry for this operation

    with db_name_to_client["write"].yield_session() as write_session:
        pass

        # Write the entitry to the write database first

        # Write the Event to the write database

    # if needed, transform the entity into its equivalent read DB representation

    # Write the entity to the read database
