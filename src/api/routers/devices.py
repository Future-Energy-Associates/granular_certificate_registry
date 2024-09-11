# Imports
import os
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.api import utils
from src.api.routers import authentication
from src.datamodel import db
from src.datamodel.schemas import entities

environment = os.getenv("ENVIRONMENT")


# Router initialisation
router = APIRouter(tags=["Devices"])


def process_uuid(uuid_: uuid.UUID):
    if environment == "STAGE":
        uuid_ = str(uuid_).replace("-", "")

    return uuid_


### Device ###


@router.post("/device", response_model=entities.DeviceRead)
def create_device(
    device: entities.DeviceBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = entities.Device.create(device, session)

    return utils.format_json_response(
        db_device, headers, response_model=entities.DeviceRead
    )


@router.get("/device/{device_id}", response_model=entities.DeviceRead)
def read_device(
    device_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = entities.Device.by_id(process_uuid(device_id), session)

    return utils.format_json_response(
        db_device, headers, response_model=entities.DeviceRead
    )


@router.patch("/device/{device_id}", response_model=entities.DeviceRead)
def update_device(
    device: entities.DeviceUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = entities.Device.by_id(process_uuid(device.device_id), session)
    db_device.update(device, session)

    return utils.format_json_response(
        db_device, headers, response_model=entities.DeviceRead
    )


@router.delete("/device/{device_id}", response_model=entities.DeviceRead)
def delete_device(
    device_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_device = entities.Device.by_id(device_id, session)
    db_device.delete(session)

    return utils.format_json_response(
        db_device, headers, response_model=entities.DeviceRead
    )