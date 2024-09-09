from fastapi import APIRouter, Depends
from gc_registry import utils
from gc_registry.database import db
from gc_registry.schemas import account
from sqlmodel import Session

from . import authentication

# Router initialisation
router = APIRouter(tags=["Accounts"])


### Account ###
@router.post("/account", response_model=account.AccountRead)
def create_account(
    account_base: account.AccountBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = account.Account.create(account_base, session)

    return utils.format_json_response(
        db_account, headers, response_model=account.AccountRead
    )


@router.get("/account/{account_id}", response_model=account.AccountRead)
def read_account(
    account_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = account.Account.by_id(account_id, session)

    return utils.format_json_response(
        db_account, headers, response_model=account.AccountRead
    )


@router.patch("/account/{account_id}", response_model=account.AccountRead)
def update_account(
    account_update: account.AccountUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = account.Account.by_id(account_update.account_id, session)
    db_account.update(account_update, session)

    return utils.format_json_response(
        db_account, headers, response_model=account.AccountRead
    )


@router.delete("/account/{account_id}", response_model=account.AccountRead)
def delete_account(
    account_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_account = account.Account.by_id(account_id, session)
    db_account.delete(session)

    return utils.format_json_response(
        db_account, headers, response_model=account.AccountRead
    )
