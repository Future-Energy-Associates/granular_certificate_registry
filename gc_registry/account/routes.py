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
    # headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].get_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].get_session),
):
    print("Creating account: ", account_base)
    db_account = models.Account.create(account_base, write_session, read_session)

    return utils.format_json_response(
        db_account, headers=None, response_model=models.AccountRead
    )


@router.get("/account/{account_id}", response_model=models.AccountRead)
def read_account(
    account_id: int,
    # headers: dict = Depends(services.validate_user_and_get_headers),
    read_session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    with next(db.db_name_to_client["db_write"].yield_session()) as write_session:
        db_account = models.Account.by_id(account_id, write_session)

    return utils.format_json_response(
        db_account, headers=None, response_model=models.AccountRead
    )


@router.patch("/account/{id}", response_model=models.AccountRead)
def update_account(
    account: models.AccountRead,
    account_update: models.AccountUpdate,
    # headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    account_updated = account.update(account_update, write_session, read_session)

    return utils.format_json_response(
        account_updated, headers=None, response_model=models.AccountRead
    )


@router.delete("/account/{id}", response_model=models.AccountRead)
def delete_account(
    account_id: int,
    # headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    db_account = models.Account.by_id(account_id, read_session)
    db_account = db_account.delete(write_session, read_session)

    return utils.format_json_response(
        db_account, headers=None, response_model=models.AccountRead
    )
