from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel

from gc_registry.utils import ActiveRecord


class EventTypes(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class Event(ActiveRecord, table=True):
    __tablename__ = "events"
    id: int = Field(primary_key=True)
    entity_id: int
    entity_name: str
    event_type: EventTypes
    attributes_before: dict | None = Field(sa_column=Column(JSON))
    attributes_after: dict | None = Field(sa_column=Column(JSON))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


def transform_write_entities_to_read(entities: list[SQLModel] | SQLModel):
    # TODO add transformations here when read schemas are defined
    return entities


def write_to_database(
    entities: list[SQLModel] | SQLModel, write_session: Session, read_session: Session
):
    """Write the provided entities to the read and write databases, saving an
    Event entry for each entity."""

    if not isinstance(entities, list):
        entities = [entities]

    # Create a list of Event entries for this operation
    events = [
        Event(
            entity_id=entity.id,  # type: ignore
            entity_name=entity.__class__.__name__,
            event_type=EventTypes.CREATE,
        )
        for entity in entities
    ]

    try:
        # Batch write the entities to the databases
        write_session.add_all(entities)
        write_session.add_all(events)

    except Exception as e:
        print(f"Error during commit to write DB: {str(e)}")
        write_session.rollback()
        return

    try:
        # if needed, transform the entity into its equivalent read DB representation
        read_entities = transform_write_entities_to_read(entities)
        read_entities = [read_session.merge(entity) for entity in read_entities]
        read_session.add_all(read_entities)

    except Exception as e:
        print(f"Error during commit to read DB: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return

    write_session.commit()
    read_session.commit()

    return entities


def update_database_entity(
    entity: SQLModel,
    update_entity: BaseModel,
    write_session: Session,
    read_session: Session,
):
    """Update the entity with the provided Model Update instance."""

    # TODO I can't think of a performant way to bulk update whilst also
    # tracking before/after values, will look at in the future

    update_data: dict = update_entity.model_dump(exclude_unset=True)

    # Create an Event entry for this operation
    event = Event(
        entity_id=entity.id,  # type: ignore
        entity_name=entity.__class__.__name__,
        event_type=EventTypes.UPDATE,
        attributes_before={
            attr: entity.__getattribute__(attr) for attr in update_data.keys()
        },
        attributes_after=update_data,
    )

    try:
        entity.sqlmodel_update(update_data)

        write_session.add(entity)
        write_session.add(event)

    except Exception as e:
        print(f"Error during commit to write DB: {str(e)}")
        write_session.rollback()
        return

    try:
        read_entity = read_session.merge(entity)
        read_entity = transform_write_entities_to_read(read_entity)
        read_entity_update_data: dict = read_entity.model_dump(exclude_unset=True)

        read_entity.sqlmodel_update(read_entity_update_data)

        read_session.add(read_entity)

    except Exception as e:
        print(f"Error during commit to read DB: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return

    write_session.commit()
    read_session.commit()

    return entity


def delete_database_entity(
    entity: SQLModel, write_session: Session, read_session: Session
):
    """Perform a soft delete on the provided entity."""

    # Create an Event entry for this operation
    event = Event(
        entity_id=entity.id,  # type: ignore
        entity_name=entity.__class__.__name__,
        event_type=EventTypes.DELETE,
    )

    try:
        entity.is_deleted = True
        write_session.add(entity)
        write_session.add(event)

    except Exception as e:
        print(f"Error during commit to write DB: {str(e)}")
        write_session.rollback()
        return

    try:
        read_entity = read_session.merge(entity)
        read_entity = transform_write_entities_to_read(read_entity)

        read_entity.is_deleted = True
        read_session.add(read_entity)

    except Exception as e:
        print(f"Error during commit to read DB: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return

    write_session.commit()
    read_session.commit()

    return entity
