from sqlmodel import Session

from gc_registry.account import models


def test_by_id(
    db_read_session: Session, db_write_session: Session, fake_db_account: models.Account
):
    assert fake_db_account.id is not None

    account_in_db = models.Account.by_id(fake_db_account.id, db_read_session)

    assert account_in_db is not None
    assert account_in_db.account_name == fake_db_account.account_name
