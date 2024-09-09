from __future__ import annotations

import uuid as uuid_pkg
from typing import List, Optional

from sqlmodel import Field, Relationship

from src.schemas import user_account_link, utils

# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.


class AccountBase(utils.ActiveRecord):
    account_name: str


class Account(AccountBase, table=True):
    account_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    users: list["User"] = Relationship(
        back_populates="accounts", link_model=user_account_link.UserAccountLink
    )
    devices: list["Device"] = Relationship(back_populates="devices")


class AccountRead(AccountBase):
    account_id: uuid_pkg.UUID
    users: list["User"]


class AccountUpdate(AccountBase):
    account_name: Optional[str]
    account_id: Optional[uuid_pkg.UUID]


# Manually define forward annotations
Account.__annotations__["users"] = List["src.schemas.user.User"]
Account.__annotations__["devices"] = List["src.schemas.device.Device"]
AccountRead.__annotations__["users"] = List["src.schemas.user.User"]
