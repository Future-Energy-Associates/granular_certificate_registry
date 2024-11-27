from fastapi import HTTPException
from sqlmodel import Session

from gc_registry.account.models import Account, AccountWhitelist
from gc_registry.user.models import User


def validate_account(account, read_session):
    # Make sure operations cannot be performed on deleted accounts
    if account.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot update deleted accounts.")

    # Account names must be unique
    account_exists = (
        read_session.query(Account)
        .filter(Account.account_name == account.account_name)
        .exists()
    )
    if account_exists.scalar():
        raise HTTPException(
            status_code=400, detail="Account name already exists in the database."
        )

    # All user_ids linked to the account must exist in the database
    user_ids_in_db = (
        read_session.query(User.id).filter(User.id.in_(account.user_ids)).all()
    )
    if len(user_ids_in_db) != len(account.user_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more users assinged to this account do not exist in the database.",
        )


def validate_account_whitelist_update(
    account: Account, account_whitelist_update: AccountWhitelist, read_session: Session
):
    """Ensure that the account whitelist update is valid by checking that the accounts in question exist.

    Args:
        account (Account): The account to be updated.
        account_whitelist_update (AccountWhitelist): The whitelist update to be applied.
        read_session (Session): The database session to read from.

    Returns:
        modified_whitelist: The modified whitelist to be applied to the account.
    """
    if account_whitelist_update.add_to_whitelist is not None:
        for account_id_to_add in account_whitelist_update.add_to_whitelist:
            if not Account.exists(account_id_to_add, read_session):
                raise HTTPException(
                    status_code=404,
                    detail=f"Account ID to add not found: {account_id_to_add}",
                )
        modified_whitelist = list(
            set(account.user_ids + account_whitelist_update.add_to_whitelist)
        )

    if account_whitelist_update.remove_from_whitelist is not None:
        modified_whitelist = list(
            set(account.user_ids) - set(account_whitelist_update.remove_from_whitelist)
        )

    return modified_whitelist
