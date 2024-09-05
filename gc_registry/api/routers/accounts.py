# Imports
import os

from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.api import utils
from gc_registry.datamodel import db
from gc_registry.datamodel.schemas import entities

from . import authentication

environment = os.getenv("ENVIRONMENT")


# Router initialisation
router = APIRouter(tags=["Accounts"])


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
    account_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = entities.Account.by_id(account_id, session)

    return utils.format_json_response(
        db_account, headers, response_model=entities.AccountRead
    )


@router.patch("/account/{account_id}", response_model=entities.AccountRead)
def update_account(
    account: entities.AccountUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    if account.id is None:
        raise ValueError("Account ID is required for update")

    db_account = entities.Account.by_id(account.id, session)
    db_account.update(account, session)

    return utils.format_json_response(
        db_account, headers, response_model=entities.AccountRead
    )


@router.delete("/account/{account_id}", response_model=entities.AccountRead)
def delete_account(
    account_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = entities.Account.by_id(account_id, session)
    db_account.delete(session)

    return utils.format_json_response(
        db_account, headers, response_model=entities.AccountRead
    )
