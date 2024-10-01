from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.account import models, services
from gc_registry.core.database import db

# Router initialisation
router = APIRouter(tags=["Accounts"])


### Account ###
@router.post("/create", status_code=201, response_model=models.AccountRead)
def create_account(
    account_base: models.AccountBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
):
    # services.validate_account(account_base, read_session)
    print("create_account")
    account = models.Account.create(account_base, write_session, read_session)
    print("account:", account)
    return account


@router.get("/{account_id}", response_model=models.AccountRead)
def read_account(
    account_id: int,
    read_session: Session = Depends(db.get_read_session),
):
    account = models.Account.by_id(account_id, read_session)

    return account


@router.patch("/update/{account_id}", response_model=models.AccountRead)
def update_account(
    account_id: int,
    account_update: models.AccountUpdate,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
):
    account = models.Account.by_id(account_id, write_session())
    services.validate_account(account_update, read_session())

    return account.update(account_update, write_session(), read_session())


@router.delete("/delete/{account_id}", status_code=204)
def delete_account(
    account_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
):
    account = models.Account.by_id(account_id, write_session())
    return account.delete(write_session(), read_session())
