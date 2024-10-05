from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from gc_registry.account import models
from gc_registry.core.database import db, events

# Router initialisation
router = APIRouter(tags=["Accounts"])


@router.post("/create", status_code=201, response_model=models.AccountRead)
def create_account(
    account_base: models.AccountBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    # services.validate_account(account_base, read_session)
    accounts = models.Account.create(
        account_base, write_session, read_session, esdb_client
    )
    if not accounts:
        raise HTTPException(status_code=500, detail="Could not create Account")

    account = accounts[0].model_dump()

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
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    try:
        account = models.Account.by_id(account_id, write_session)
        updated_account = account.update(
            account_update, write_session, read_session, esdb_client
        )
        if not updated_account:
            raise ValueError(f"Account id {account_id} not found")
        return updated_account.model_dump()
    except Exception:
        raise HTTPException(status_code=404, detail="Could not update Account")


@router.delete(
    "/delete/{account_id}", status_code=200, response_model=models.AccountRead
)
def delete_account(
    account_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    try:
        account = models.Account.by_id(account_id, write_session)
        accounts = account.delete(write_session, read_session, esdb_client)
        if not accounts:
            raise ValueError(f"Account id {account_id} not found")
        return accounts[0].model_dump()
    except Exception:
        raise HTTPException(
            status_code=404, detail="Could not delete Account not found"
        )
