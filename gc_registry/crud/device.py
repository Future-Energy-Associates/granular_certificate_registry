# Imports
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.crud import authentication
from gc_registry.database import db
from gc_registry.schemas import device

# Router initialisation
router = APIRouter(tags=["Devices"])

### Device ###


@router.post("/device", response_model=device.DeviceRead)
def create_device(
    device_base: device.DeviceBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.create(device_base, session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )


@router.get("/device/{id}", response_model=device.DeviceRead)
def read_device(
    device_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.by_id(device_id, session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )


@router.patch("/device/{id}", response_model=device.DeviceRead)
def update_device(
    device_update: device.DeviceUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.by_id(device_update.id, session)
    db_device.update(device_update, session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )


@router.delete("/device/{id}", response_model=device.DeviceRead)
def delete_device(
    device_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.by_id(device_id, session)
    db_device.delete(session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )
