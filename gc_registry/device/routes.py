# Imports
from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from gc_registry.authentication.services import get_current_user
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.device import models
from gc_registry.logging_config import log_context, logger
from gc_registry.user.models import User
from gc_registry.user.validation import validate_user_access, validate_user_role

# Router initialisation
router = APIRouter(tags=["Devices"])


@router.post("/create", response_model=models.DeviceRead)
def create_device(
    device_create: models.DeviceCreate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Only production users can create devices and associate them with an account they control."""
    with log_context(
        operation="create_device",
        user_id=current_user.id,
        account_id=device_create.account_id,
    ):
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)
        validate_user_access(current_user, device_create.account_id, read_session)

        devices = models.Device.create(
            device_create, write_session, read_session, esdb_client
        )
        if not devices:
            raise HTTPException(status_code=500, detail="Could not create Device")

        device = devices[0].model_dump()

        logger.info("Device created successfully", extra={"device_id": device["id"]})

        return device


@router.get("/{device_id}", response_model=models.DeviceRead)
def read_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)
    device = models.Device.by_id(device_id, read_session)

    validate_user_access(current_user, device.account_id, read_session)

    return device


@router.patch("/update/{device_id}", response_model=models.DeviceRead)
def update_device(
    device_id: int,
    device_update: models.DeviceUpdate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    with log_context(
        operation="update_device",
        device_id=device_id,
        user_id=current_user.id,
    ):
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)
        device = models.Device.by_id(device_id, read_session)

        validate_user_access(current_user, device.account_id, read_session)

        updated_device = device.update(device_update, write_session, read_session, esdb_client)
        logger.info("Device updated successfully")
        return updated_device


@router.delete("/delete/{device_id}", response_model=models.DeviceRead)
def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    with log_context(
        operation="delete_device",
        device_id=device_id,
        user_id=current_user.id,
    ):
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)
        device = models.Device.by_id(device_id, write_session)

        validate_user_access(current_user, device.account_id, read_session)

        deleted_device = device.delete(write_session, read_session, esdb_client)
        logger.info("Device deleted successfully")
        return deleted_device
