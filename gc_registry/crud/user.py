from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.crud import authentication
from gc_registry.database import db
from gc_registry.schemas import user

# Router initialisation
router = APIRouter(tags=["Users"])

### User ###


@router.post("/user", response_model=user.UserRead)
def create_user(
    user_base: user.UserBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.create(user_base, session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)


@router.get("/user/{user_id}", response_model=user.UserRead)
def read_user(
    user_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.by_id(user_id, session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)


@router.patch("/user/{user_id}", response_model=user.UserRead)
def update_user(
    user_update: user.UserUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.by_id(user_update.user_id, session)
    db_user.update(user_update, session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)


@router.delete("/user/{user_id}", response_model=user.UserRead)
def delete_user(
    user_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = user.User.by_id(user_id, session)
    db_user.delete(session)

    return utils.format_json_response(db_user, headers, response_model=user.UserRead)
