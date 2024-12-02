from typing import List

from pydantic import BaseModel
from sqlalchemy import ARRAY, Column, Integer
from sqlmodel import Field

from gc_registry import utils


class AccountBase(utils.ActiveRecord):
    account_name: str
    user_ids: List[int] | None = Field(
        default=None,
        description="The users registered to the account.",
        sa_column=Column(ARRAY(Integer())),
    )
    account_whitelist: List[int | None] | None = Field(
        default=None,
        description="The list of accounts that are allowed to transfer certificates to this account.",
        sa_column=Column(ARRAY(Integer())),
    )
    is_deleted: bool = Field(default=False)


class AccountUpdate(BaseModel):
    account_name: str | None = None
    user_ids: List[int] | None = None
    account_whitelist: List[int] | None = None


class AccountWhitelist(BaseModel):
    add_to_whitelist: List[int] | None = None
    remove_from_whitelist: List[int] | None = None
