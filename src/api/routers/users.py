# Imports
import os
from fastapi import Depends, APIRouter
from sqlmodel import Session
from energytag.api import utils
from energytag.datamodel import db
from energytag.datamodel.schemas import entities
from energytag.api.routers import authentication
import uuid


environment = os.getenv("ENVIRONMENT")


# Router initialisation
router = APIRouter(tags=["Users"])


def process_uuid(uuid_: uuid.UUID):
    if environment == "STAGE":
        uuid_ = str(uuid_).replace("-", "")

    return uuid_


### User ###


@router.post("/user", response_model=entities.UserRead)
def create_user(
    user: entities.UserBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_user = entities.User.create(user, session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )


@router.get("/user/{user_id}", response_model=entities.UserRead)
def read_user(
    user_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_user = entities.User.by_id(process_uuid(user_id), session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )


@router.patch("/user/{user_id}", response_model=entities.UserRead)
def update_user(
    user: entities.UserUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_user = entities.User.by_id(process_uuid(user.user_id), session)
    db_user.update(user, session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )


@router.delete("/user/{user_id}", response_model=entities.UserRead)
def delete_user(
    user_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_user = entities.User.by_id(user_id, session)
    db_user.delete(session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )
