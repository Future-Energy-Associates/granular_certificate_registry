from typing import TYPE_CHECKING, List

from pydantic import BaseModel
from sqlmodel import Field, Relationship

from gc_registry.account.schemas import AccountBase
from gc_registry.user.models import UserAccountLink

if TYPE_CHECKING:
    from gc_registry.device.models import Device
    from gc_registry.user.models import User

# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.


class Account(AccountBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    users: List["User"] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    devices: List["Device"] = Relationship(back_populates="account")


class AccountRead(AccountBase):
    id: int


class AccountUpdate(BaseModel):
    id: int
    account_name: str | None
    user_id: int | None
