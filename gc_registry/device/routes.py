# Imports
from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.core.database import db, events
from gc_registry.device import models

# Router initialisation
router = APIRouter(tags=["Devices"])


@router.post("/create", response_model=models.DeviceRead)
def create_device(
    device_base: models.DeviceBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    device = models.Device.create(device_base, write_session, read_session, esdb_client)

    return device


@router.get("/{device_id}", response_model=models.DeviceRead)
def read_device(
    device_id: int,
    read_session: Session = Depends(db.get_read_session),
):
    device = models.Device.by_id(device_id, read_session)

    return device


@router.patch("/update/{device_id}", response_model=models.DeviceRead)
def update_device(
    device_id: int,
    device_update: models.DeviceUpdate,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    device = models.Device.by_id(device_id, read_session)

    return device.update(device_update, write_session, read_session, esdb_client)


@router.delete("/delete/{device_id}", response_model=models.DeviceRead)
def delete_device(
    device_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    device = models.Device.by_id(device_id, write_session)
    return device.delete(write_session, read_session, esdb_client)
