from esdbclient import EventStoreDBClient
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select

from gc_registry.account.models import Account, AccountWhitelistLink
from gc_registry.account.schemas import (
    AccountBase,
    AccountWhitelist,
)
from gc_registry.user.models import User


def validate_account(account: Account | AccountBase, read_session: Session):
    """Validates account creation and update requests."""

    # Account names must be unique and case insensitive
    account_exists = read_session.exec(
        select(Account).filter(
            func.lower(Account.account_name) == func.lower(account.account_name)
        )
    ).first()

    if account_exists is not None:
        raise HTTPException(
            status_code=400, detail="Account name already exists in the database."
        )

    # All user_ids linked to the account must exist in the database
    if account.user_ids is not None:
        user_ids_in_db = read_session.exec(
            select(User.id).filter(User.id.in_(account.user_ids))  # type: ignore
        ).all()
        user_ids_in_db_set = set(user_ids_in_db)
        if user_ids_in_db_set != set(account.user_ids):
            raise HTTPException(
                status_code=400,
                detail="One or more users assigned to this account do not exist in the database.",
            )


def validate_and_apply_account_whitelist_update(
    account: Account,
    account_whitelist_update: AccountWhitelist,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
):
    """Ensure that the account whitelist update is valid by checking that the accounts in question exist,
    and writes to the whitelist link table if the update is valid.

    Args:
        account (Account): The account to be updated.
        account_whitelist_update (AccountWhitelist): The whitelist update to be applied.
        read_session (Session): The database session to read from.
        write_session (Session): The database session to write to.
        esdb_client (EventStoreDBClient): The EventStoreDB client to use for event sourcing.
    """
    existing_whitelist = read_session.exec(
        select(AccountWhitelistLink.source_account_id).where(
            AccountWhitelistLink.target_account_id == account.id
        )
    ).all()

    if account_whitelist_update.add_to_whitelist is not None:
        for account_id_to_add in account_whitelist_update.add_to_whitelist:
            if account_id_to_add == account.id:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot add an account to its own whitelist.",
                )
            if not Account.exists(account_id_to_add, read_session):
                raise HTTPException(
                    status_code=404,
                    detail=f"Account ID to add not found: {account_id_to_add}",
                )
            if (existing_whitelist is not None) and (
                account_id_to_add in existing_whitelist
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Account ID {account_id_to_add} is already in the whitelist.",
                )
            AccountWhitelistLink.create(
                {
                    "target_account_id": account.id,
                    "source_account_id": account_id_to_add,
                },
                write_session=write_session,
                read_session=read_session,
                esdb_client=esdb_client,
            )

    if account_whitelist_update.remove_from_whitelist is not None:
        for account_id_to_remove in account_whitelist_update.remove_from_whitelist:
            if not Account.exists(account_id_to_remove, read_session):
                raise HTTPException(
                    status_code=404,
                    detail=f"Account ID to remove not found: {account_id_to_remove}",
                )
            account_whitelist_link_to_remove = read_session.exec(
                select(AccountWhitelistLink).where(
                    AccountWhitelistLink.target_account_id == account.id,
                    AccountWhitelistLink.source_account_id == account_id_to_remove,
                    AccountWhitelistLink.is_deleted == False,  # noqa: E712
                )
            ).first()
            if account_whitelist_link_to_remove is not None:
                account_whitelist_link_to_remove.delete(
                    write_session=write_session,
                    read_session=read_session,
                    esdb_client=esdb_client,
                )
