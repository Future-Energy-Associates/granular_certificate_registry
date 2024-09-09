# Imports
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src import utils
from src.crud import authentication
from src.database import db
from src.schemas import user

# Router initialisation
router = APIRouter(tags=["Users"])

### User ###


@router.post("/user", response_model=user.UserRead)
def create_user(
    user: user.UserBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.create(user, session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)


@router.get("/user/{user_id}", response_model=user.UserRead)
def read_user(
    user_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.by_id(utils.process_uuid(user_id), session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)


@router.patch("/user/{user_id}", response_model=user.UserRead)
def update_user(
    user: user.UserUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.by_id(utils.process_uuid(user.user_id), session)
    db_user.update(user, session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)


@router.delete("/user/{user_id}", response_model=user.UserRead)
def delete_user(
    user_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.by_id(user_id, session)
    db_user.delete(session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)
