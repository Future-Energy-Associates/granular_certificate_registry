# Imports
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src import utils
from src.crud import authentication
from src.database import db
from src.schemas import device

# Router initialisation
router = APIRouter(tags=["Devices"])

### Device ###


@router.post("/device", response_model=device.DeviceRead)
def create_device(
    device: device.DeviceBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.create(device, session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )


@router.get("/device/{device_id}", response_model=device.DeviceRead)
def read_device(
    device_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.by_id(utils.process_uuid(device_id), session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )


@router.patch("/device/{device_id}", response_model=device.DeviceRead)
def update_device(
    device: device.DeviceUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.by_id(utils.process_uuid(device.device_id), session)
    db_device.update(device, session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )


@router.delete("/device/{device_id}", response_model=device.DeviceRead)
def delete_device(
    device_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = device.Device.by_id(device_id, session)
    db_device.delete(session)

    return utils.format_json_response(
        db_device, headers, response_model=device.DeviceRead
    )
