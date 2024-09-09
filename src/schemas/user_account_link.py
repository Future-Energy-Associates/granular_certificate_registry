import uuid as uuid_pkg
from typing import (
    Optional,
)

from sqlmodel import Field

from src.schemas import utils


class UserAccountLink(utils.ActiveRecord, table=True):
    user_id: Optional[uuid_pkg.UUID] = Field(
        default=None, foreign_key="user.user_id", primary_key=True
    )
    account_id: Optional[uuid_pkg.UUID] = Field(
        default=None, foreign_key="account.account_id", primary_key=True
    )
