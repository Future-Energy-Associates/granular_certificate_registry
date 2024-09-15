from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.authentication import services
from gc_registry.core.database import db
from gc_registry.user import models

# Router initialisation
router = APIRouter(tags=["Users"])

### User ###


@router.post("/user", response_model=models.UserRead)
def create_user(
    user_base: models.UserBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_user = models.User.create(user_base, session)

    return utils.format_json_response(db_user, headers, response_model=models.UserRead)


@router.get("/user/{id}", response_model=models.UserRead)
def read_user(
    user_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_user = models.User.by_id(user_id, session)

    return utils.format_json_response(db_user, headers, response_model=models.UserRead)


@router.patch("/user/{id}", response_model=models.UserRead)
def update_user(
    user_update: models.UserUpdate,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_user = models.User.by_id(user_update.id, session)
    db_user.update(user_update, session)

    return utils.format_json_response(db_user, headers, response_model=models.UserRead)


@router.delete("/user/{id}", response_model=models.UserRead)
def delete_user(
    user_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_user = models.User.by_id(user_id, session)
    db_user.delete(session)

    return utils.format_json_response(db_user, headers, response_model=models.UserRead)
