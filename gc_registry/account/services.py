from fastapi import HTTPException
from sqlalchemy import select

from gc_registry.account.models import Account
from gc_registry.user.models import User


def get_account_by_id(account_id, read_session):
    stmt = select(Account).where(Account.id == account_id)
    account = read_session.exec(stmt).first()
    return account


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
