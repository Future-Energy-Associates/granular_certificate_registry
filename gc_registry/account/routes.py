from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.account import models
from gc_registry.authentication import services
from gc_registry.core.database import db

# Router initialisation
router = APIRouter(tags=["Accounts"])


### Account ###
@router.post("/create", status_code=201)
def create_account(
    account_base: models.AccountBase,
    # headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].get_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].get_session),
):
    models.Account.create(account_base, write_session, read_session)

    return {"message": f"Account {account_base.account_name} created successfully."}


@router.get("/{account_id}", response_model=models.AccountRead)
def read_account(
    account_id: int,
    # headers: dict = Depends(services.validate_user_and_get_headers),
    read_session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    account = models.Account.by_id(account_id, read_session)

    return utils.format_json_response(
        account, headers=None, response_model=models.AccountRead
    )


@router.patch("/update/{account_id}", response_model=models.AccountRead)
def update_account(
    account_id: int,
    account_update: models.AccountUpdate,
    # headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].get_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].get_session),
):
    account = models.Account.by_id(account_id, write_session)
    account_updated = account.update(account_update, write_session, read_session)

    return utils.format_json_response(
        account_updated, headers=None, response_model=models.AccountRead
    )


@router.delete("/delete/{account_id}", status_code=204)
def delete_account(
    account_id: int,
    # headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].get_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].get_session),
):
    account = models.Account.by_id(account_id, write_session)
    _account_deleted = account.delete(write_session, read_session)

    return {"message": f"Account {account_id} deleted successfully."}
