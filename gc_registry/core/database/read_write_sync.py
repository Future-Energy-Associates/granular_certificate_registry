from datetime import datetime

from fastapi import APIRouter, BackgroundTasks
from sqlalchemy import Column, DateTime, Integer, String, func
from sqlmodel import SQLModel

from gc_registry.core.database.db import db_name_to_client

router = APIRouter(tags=["Sync"])


class Event(SQLModel, table=True):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer)
    event_type = Column(String)
    data = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


# This will be updated to capture the specific entity that was updated
class Entity(SQLModel, table=True):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True)
    data = Column(String)


async def sync_databases():
    write_session = db_name_to_client["write"].yield_session()
    read_session = db_name_to_client["read"].yield_session()

    try:
        # Get the last processed event ID from the read database
        last_processed_id = read_session.query(func.max(Event.id)).scalar() or 0

        # Fetch new events from the write database
        new_events = (
            write_session.query(Event)
            .filter(Event.id > last_processed_id)
            .order_by(Event.id)
            .all()
        )

        for event in new_events:
            # Process each event and update the read database accordingly
            if event.event_type == "CREATE":
                # Create a new entity in the read database
                new_entity = Entity(id=event.entity_id, data=event.data)
                read_session.add(new_entity)
            elif event.event_type == "UPDATE":
                # Update an existing entity in the read database
                entity = (
                    read_session.query(Entity).filter_by(id=event.entity_id).first()
                )
                if entity:
                    entity.data = event.data
            elif event.event_type == "DELETE":
                # Delete an entity from the read database
                entity = (
                    read_session.query(Entity).filter_by(id=event.entity_id).first()
                )
                if entity:
                    read_session.delete(entity)

        read_session.commit()
    except Exception as e:
        print(f"Error during synchronization: {str(e)}")
        read_session.rollback()
    finally:
        write_session.close()
        read_session.close()


@router.post("/trigger-sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_databases)
    return {"message": "Read/Write Synchronization triggered"}
