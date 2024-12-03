from fastapi import HTTPException
from sqlmodel import Session, select

from gc_registry.account.models import Account
from gc_registry.account.schemas import AccountWhitelist
from gc_registry.user.models import User


def validate_account(account, read_session):
    # Make sure operations cannot be performed on deleted accounts
    if account.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot update deleted accounts.")

    # Account names must be unique
    account_exists_query = (
        select(Account).filter(Account.account_name == account.account_name).exists()
    )
    account_exists = read_session.execute(select(account_exists_query)).scalar()

    if account_exists:
        raise HTTPException(
            status_code=400, detail="Account name already exists in the database."
        )

    # All user_ids linked to the account must exist in the database
    stmt = select(User.id).filter(User.id.in_(account.user_ids))
    user_ids_in_db = read_session.execute(stmt).scalars().all()

    if set(user_ids_in_db) != set(account.user_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more users assigned to this account do not exist in the database.",
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
    existing_user_ids = [] if account.user_ids is None else account.user_ids

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
        modified_whitelist = list(
            set(existing_user_ids + account_whitelist_update.add_to_whitelist)  # type: ignore
        )

    if account_whitelist_update.remove_from_whitelist is not None:
        modified_whitelist = list(
            set(existing_user_ids) - set(account_whitelist_update.remove_from_whitelist)  # type: ignore
        )

    return modified_whitelist
