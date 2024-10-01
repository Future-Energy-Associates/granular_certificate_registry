from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.core.database import db, events
from gc_registry.user import models

# Router initialisation
router = APIRouter(tags=["Users"])

### User ###


@router.post("/create", response_model=models.UserRead)
def create_user(
    user_base: models.UserBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    user = models.User.create(user_base, write_session, read_session, esdb_client)

    return user


@router.get("/{user_id}", response_model=models.UserRead)
def read_user(
    user_id: int,
    read_session: Session = Depends(db.get_read_session),
):
    user = models.User.by_id(user_id, read_session)

    return user


@router.patch("/update/{user_id}", response_model=models.UserRead)
def update_user(
    user_id: int,
    user_update: models.UserUpdate,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    user = models.User.by_id(user_id, write_session)

    return user.update(user_update, write_session, read_session, esdb_client)


@router.delete("/delete/{id}", response_model=models.UserRead)
def delete_user(
    user_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    user = models.User.by_id(user_id, read_session)
    return user.delete(write_session, read_session, esdb_client)
