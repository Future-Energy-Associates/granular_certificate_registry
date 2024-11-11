from esdbclient import EventStoreDBClient
from pydantic import BaseModel
from sqlmodel import Session, SQLModel

from gc_registry.core.database.events import batch_create_events, create_event
from gc_registry.core.models.base import EventTypes


def transform_write_entities_to_read(entities: list[SQLModel] | SQLModel):
    # TODO add transformations here when read schemas are defined
    return entities


def write_to_database(
    entities: list[SQLModel] | SQLModel,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> list[SQLModel] | None:
    """Write the provided entities to the read and write databases, saving an
    Event entry for each entity."""

    if not isinstance(entities, list):
        entities = [entities]

    try:
        # Batch write the entities to the databases
        write_session.add_all(entities)
        write_session.flush()

        # Refresh write entites prior to conversion to read entities
        for entity in entities:
            write_session.refresh(entity)

    except Exception as e:
        print(
            f"Error during commit to write DB during create: {str(e)}, session ID {id(write_session)}"
        )
        write_session.rollback()
        return None

    try:
        # if needed, transform the entity into its equivalent read DB representation
        read_entities = transform_write_entities_to_read(entities)

        # merge read entities from the write session to prevent de-scoping
        read_entities = [read_session.merge(entity) for entity in read_entities]
        read_session.add_all(read_entities)
        read_session.flush()

    except Exception as e:
        print(f"Error during commit to read DB during create: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return None

    batch_create_events(
        entity_ids=[entity.id for entity in entities],  # type: ignore
        entity_names=[entity.__class__.__name__ for entity in entities],
        event_type=EventTypes.CREATE,
        esdb_client=esdb_client,
    )

    write_session.commit()
    read_session.commit()

    for entity in read_entities:
        read_session.refresh(entity)

    return read_entities


def update_database_entity(
    entity: SQLModel,
    update_entity: BaseModel,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> SQLModel | None:
    """Update the entity with the provided Model Update instance."""

    # TODO I can't think of a performant way to bulk update whilst also
    # tracking before/after values, will look at in the future

    before_data = {
        attr: entity.__getattribute__(attr)
        for attr in update_entity.model_dump(exclude_unset=True)
    }

    update_data: dict = update_entity.model_dump(exclude_unset=True)

    try:
        entity.sqlmodel_update(update_data)

        write_session.add(entity)
        write_session.flush()
        write_session.refresh(entity)

    except Exception as e:
        print(f"Error during commit to write DB during update: {str(e)}")
        write_session.rollback()
        return None

    try:
        read_entity = transform_write_entities_to_read(entity)
        read_entity = read_session.merge(read_entity)

        read_session.add(read_entity)
        read_session.flush()

    except Exception as e:
        print(f"Error during commit to read DB during update: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return None

    create_event(
        entity_id=entity.id,  # type: ignore
        entity_name=entity.__class__.__name__,
        event_type=EventTypes.UPDATE,
        attributes_before=before_data,
        attributes_after=update_data,
        esdb_client=esdb_client,
    )

    write_session.commit()
    read_session.commit()

    read_session.refresh(read_entity)

    return read_entity


def delete_database_entities(
    entities: list[SQLModel] | SQLModel,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> list[SQLModel] | None:
    """Perform a soft delete on the provided entities."""

    if not isinstance(entities, list):
        entities = [entities]

    try:
        for entity in entities:
            entity.is_deleted = True

        write_session.add_all(entities)
        write_session.flush()
        for entity in entities:
            write_session.refresh(entity)

    except Exception as e:
        print(f"Error during commit to write DB during delete: {str(e)}")
        write_session.rollback()
        return None

    try:
        read_entities = transform_write_entities_to_read(entities)
        read_entities = [read_session.merge(entity) for entity in read_entities]
        for read_entity in read_entities:
            read_entity.is_deleted = True
        read_session.add_all(read_entities)
        read_session.flush()

    except Exception as e:
        print(f"Error during commit to read DB during delete: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return None

    batch_create_events(
        entity_ids=[entity.id for entity in entities],  # type: ignore
        entity_names=[entity.__class__.__name__ for entity in entities],
        event_type=EventTypes.DELETE,
        esdb_client=esdb_client,
    )

    write_session.commit()
    read_session.commit()

    for entity in read_entities:
        read_session.refresh(entity)

    return read_entities
