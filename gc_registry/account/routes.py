from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from gc_registry.account import models
from gc_registry.account.validation import (
    validate_account,
    validate_account_whitelist_update,
)
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
    validate_account(account_base, read_session)
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
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/update/{account_id}", response_model=models.AccountRead)
def update_account(
    account_id: int,
    account_update: models.AccountUpdate,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    account = models.Account.by_id(account_id, write_session)
    if not account:
        raise HTTPException(
            status_code=404, detail=f"Account ID not found: {account_id}"
        )

    updated_account = account.update(
        account_update, write_session, read_session, esdb_client
    )
    if not updated_account:
        raise HTTPException(
            status_code=400, detail=f"Error during account update: {account_id}"
        )
    return updated_account.model_dump()


@router.patch("/update_whitelist/{account_id}", response_model=models.AccountRead)
def update_whitelist(
    account_id: int,
    account_whitelist_update: models.AccountWhitelist,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    account = models.Account.by_id(account_id, write_session)
    if not account:
        raise HTTPException(
            status_code=404, detail=f"Account ID not found: {account_id}"
        )

    modified_whitelist = validate_account_whitelist_update(
        account, account_whitelist_update, read_session
    )

    account_update = models.AccountUpdate(account_whitelist=modified_whitelist)

    updated_account = account.update(
        account_update, write_session, read_session, esdb_client
    )
    if not updated_account:
        raise HTTPException(
            status_code=400, detail=f"Error during account update: {account_id}"
        )
    return updated_account.model_dump()


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
