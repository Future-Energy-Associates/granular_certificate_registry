# Imports
import os
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.api import utils
from src.datamodel import db
from src.datamodel.schemas import entities

from . import authentication

environment = os.getenv("ENVIRONMENT")


# Router initialisation
router = APIRouter(tags=["Accounts"])


def process_uuid(uuid_: uuid.UUID):
    if environment == "STAGE":
        uuid_ = str(uuid_).replace("-", "")

    return uuid_


### Account ###


@router.post("/account", response_model=entities.AccountRead)
def create_account(
    account: entities.AccountBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = entities.Account.create(account, session)

    return utils.format_json_response(
        db_account, headers, response_model=entities.AccountRead
    )


@router.get("/account/{account_id}", response_model=entities.AccountRead)
def read_account(
    account_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = entities.Account.by_id(process_uuid(account_id), session)

    return utils.format_json_response(
        db_account, headers, response_model=entities.AccountRead
    )


@router.patch("/account/{account_id}", response_model=entities.AccountRead)
def update_account(
    account: entities.AccountUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = entities.Account.by_id(process_uuid(account.account_id), session)
    db_account.update(account, session)

    return utils.format_json_response(
        db_account, headers, response_model=entities.AccountRead
    )


@router.delete("/account/{account_id}", response_model=entities.AccountRead)
def delete_account(
    account_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = entities.Account.by_id(account_id, session)
    db_account.delete(session)

    return utils.format_json_response(
        db_account, headers, response_model=entities.AccountRead
    )
