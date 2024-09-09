import uuid as uuid_pkg
from typing import (
    Optional,
)

from sqlmodel import Field, Relationship

from src.schemas import user, utils

# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.


class AccountBase(utils.ActiveRecord):
    account_name: str


class Account(AccountBase, table=True):
    account_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    users: list["User"] = Relationship(  # noqa
        back_populates="accounts", link_model=user.UserAccountLink
    )
    devices: list["Device"] = Relationship(back_populates="devices")  # noqa


class AccountRead(AccountBase):
    account_id: uuid_pkg.UUID
    users: list["User"]  # noqa


class AccountUpdate(AccountBase):
    account_name: Optional[str]
    account_id: Optional[uuid_pkg.UUID]
