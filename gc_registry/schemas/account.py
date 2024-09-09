from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from gc_registry.models.account import AccountBase
from gc_registry.schemas.user_account_link import UserAccountLink

if TYPE_CHECKING:
    from gc_registry.schemas.device import Device
    from gc_registry.schemas.user import User

# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.


class Account(AccountBase, table=True):
    account_id: int = Field(primary_key=True, autoincrement=True)
    users: List["User"] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    devices: List["Device"] = Relationship(back_populates="devices")


class AccountRead(AccountBase):
    account_id: int


class AccountUpdate(AccountBase):
    account_name: str | None
    account_id: int | None
