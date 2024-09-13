from typing import List

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field

from gc_registry import utils


class AccountBase(utils.ActiveRecord):
    account_name: str
    ids: List[int] | None = Field(
        default=None,
        description="The users registered to the account.",
        sa_column=Column(ARRAY(String())),
    )