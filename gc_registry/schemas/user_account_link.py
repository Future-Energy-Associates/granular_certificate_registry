from sqlmodel import Field

from gc_registry import utils


class UserAccountLink(utils.ActiveRecord, table=True):
    user_id: int | None = Field(
        default=None, foreign_key="user.user_id", primary_key=True
    )
    account_id: int | None = Field(
        default=None, foreign_key="account.account_id", primary_key=True
    )
