from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.account import models
from gc_registry.authentication import services
from gc_registry.core.database import cqrs, db

# Router initialisation
router = APIRouter(tags=["Accounts"])


### Account ###
@router.post("/account", response_model=models.AccountRead)
def create_account(
    account_base: models.AccountBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
):
    db_account = models.Account.create(account_base, session)

    return utils.format_json_response(
        db_account, headers, response_model=models.AccountRead
    )


@router.get("/account/{id}", response_model=models.AccountRead)
def read_account(
    account_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    db_account = models.Account.by_id(account_id, session)

    return utils.format_json_response(
        db_account, headers, response_model=models.AccountRead
    )


@router.patch("/account/{id}", response_model=models.AccountRead)
def update_account(
    account: models.AccountRead,
    account_update: models.AccountUpdate,
    headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    account_updated = cqrs.update_database_entity(
        account, account_update, write_session, read_session
    )

    return utils.format_json_response(
        account_updated, headers, response_model=models.AccountRead
    )


@router.delete("/account/{id}", response_model=models.AccountRead)
def delete_account(
    account_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
):
    db_account = models.Account.by_id(account_id, session)
    db_account.delete(session)

    return utils.format_json_response(
        db_account, headers, response_model=models.AccountRead
    )
