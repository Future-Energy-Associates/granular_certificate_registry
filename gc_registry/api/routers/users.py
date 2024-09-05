# Imports
import os

from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.api import utils
from gc_registry.api.routers import authentication
from gc_registry.datamodel import db
from gc_registry.datamodel.schemas import entities

environment = os.getenv("ENVIRONMENT")


# Router initialisation
router = APIRouter(tags=["Users"])


### User ###


@router.post("/user", response_model=entities.UserRead)
def create_user(
    user: entities.UserBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = entities.User.create(user, session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )


@router.get("/user/{user_id}", response_model=entities.UserRead)
def read_user(
    user_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = entities.User.by_id(user_id, session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )


@router.patch("/user/{user_id}", response_model=entities.UserRead)
def update_user(
    user: entities.UserUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = entities.User.by_id(user.id, session)
    db_user.update(user, session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )


@router.delete("/user/{user_id}", response_model=entities.UserRead)
def delete_user(
    user_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = entities.User.by_id(user_id, session)
    db_user.delete(session)

    return utils.format_json_response(
        db_user, headers, response_model=entities.UserRead
    )
