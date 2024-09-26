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
    esdb_client: EventStoreDBClient | None = None,
) -> None:
    """Write the provided entities to the read and write databases, saving an
    Event entry for each entity."""

    if not isinstance(entities, list):
        entities = [entities]

    print(f"Writing entities to DB: {entities[0].model_dump_json()}")
    try:
        # Batch write the entities to the databases
        write_session.add_all(entities)
        print("Entities added to write session: ", entities[0].model_dump_json())
        [write_session.refresh(entity) for entity in entities]

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

    batch_create_events(
        entity_ids=[entity.id for entity in entities],  # type: ignore
        entity_names=[entity.__class__.__name__ for entity in entities],
        event_type=EventTypes.CREATE,
        esdb_client=esdb_client,
    )

    write_session.commit()
    read_session.commit()

    return


def update_database_entity(
    entity: SQLModel,
    update_entity: BaseModel,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient | None = None,
) -> None:
    """Update the entity with the provided Model Update instance."""

    # TODO I can't think of a performant way to bulk update whilst also
    # tracking before/after values, will look at in the future

    update_data: dict = update_entity.model_dump(exclude_unset=True)

    try:
        entity.sqlmodel_update(update_data)

        write_session.add(entity)
        write_session.refresh(entity)

    except Exception as e:
        print(f"Error during commit to write DB: {str(e)}")
        write_session.rollback()
        return

    try:
        read_entity = read_session.merge(entity)
        read_entity = transform_write_entities_to_read(read_entity)
        read_entity.sqlmodel_update(update_data)
        read_entity_update_data: dict = read_entity.model_dump(exclude_unset=True)

        read_entity.sqlmodel_update(read_entity_update_data)

        read_session.add(read_entity)

    except Exception as e:
        print(f"Error during commit to read DB: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return

    create_event(
        entity_id=entity.id,  # type: ignore
        entity_name=entity.__class__.__name__,
        event_type=EventTypes.UPDATE,
        attributes_before={
            attr: entity.__getattribute__(attr) for attr in update_data.keys()
        },
        attributes_after=update_data,
        esdb_client=esdb_client,
    )

    write_session.commit()
    read_session.commit()

    return


def delete_database_entities(
    entities: list[SQLModel] | SQLModel,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient | None = None,
) -> None:
    """Perform a soft delete on the provided entities."""

    if not isinstance(entities, list):
        entities = [entities]

    try:
        for entity in entities:
            entity.is_deleted = True

        write_session.add_all(entities)
        [write_session.refresh(entity) for entity in entities]

    except Exception as e:
        print(f"Error during commit to write DB: {str(e)}")
        write_session.rollback()
        return

    try:
        read_entities = transform_write_entities_to_read(entities)
        read_entities = [read_session.merge(entity) for entity in read_entities]
        for read_entity in read_entities:
            read_entity.is_deleted = True
        read_session.add_all(read_entities)

    except Exception as e:
        print(f"Error during commit to read DB: {str(e)}")
        write_session.rollback()
        read_session.rollback()
        return

    batch_create_events(
        entity_ids=[entity.id for entity in entities],  # type: ignore
        entity_names=[entity.__class__.__name__ for entity in entities],
        event_type=EventTypes.DELETE,
        esdb_client=esdb_client,
    )

    write_session.commit()
    read_session.commit()

    return
