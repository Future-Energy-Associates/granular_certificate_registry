from sqlmodel import select

from gc_registry.account.models import Account


def get_account_by_id(account_id, read_session):
    stmt = select(Account).where(Account.id == account_id)
    account = read_session.exec(stmt).first()
    return account
