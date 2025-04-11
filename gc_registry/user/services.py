from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.user.models import User, UserAccountLink


def get_users_by_account_id(
    account_id: int, read_session: Session
) -> list[User] | None:
    stmt: SelectOfScalar = (
        select(User)
        .join(UserAccountLink)
        .where(
            UserAccountLink.account_id == account_id,
            UserAccountLink.is_deleted == False,  # noqa: E712
        )
    )
    users = read_session.exec(stmt).all()
    return list(users)
