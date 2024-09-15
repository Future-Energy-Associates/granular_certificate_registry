# Imports
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.authentication import services
from gc_registry.core.database import db
from gc_registry.device import models

# Router initialisation
router = APIRouter(tags=["Devices"])

### Device ###


@router.post("/device", response_model=models.DeviceRead)
def create_device(
    device_base: models.DeviceBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_device = models.Device.create(device_base, session)

    return utils.format_json_response(
        db_device, headers, response_model=models.DeviceRead
    )


@router.get("/device/{id}", response_model=models.DeviceRead)
def read_device(
    device_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = models.Device.by_id(device_id, session)

    return utils.format_json_response(
        db_device, headers, response_model=models.DeviceRead
    )


@router.patch("/device/{id}", response_model=models.DeviceRead)
def update_device(
    device_update: models.DeviceUpdate,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_device = models.Device.by_id(device_update.id, session)
    db_device.update(device_update, session)

    return utils.format_json_response(
        db_device, headers, response_model=models.DeviceRead
    )


@router.delete("/device/{id}", response_model=models.DeviceRead)
def delete_device(
    device_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_device = models.Device.by_id(device_id, session)
    db_device.delete(session)

    return utils.format_json_response(
        db_device, headers, response_model=models.DeviceRead
    )
