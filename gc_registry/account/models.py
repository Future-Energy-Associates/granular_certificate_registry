from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from gc_registry import utils
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
    users: list["User"] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    devices: list["Device"] = Relationship(back_populates="account")


class AccountWhitelistLink(utils.ActiveRecord, table=True):
    id: int | None = Field(
        default=None, primary_key=True, description="A unique ID assigned to this link."
    )
    target_account_id: int
    source_account_id: int
    is_deleted: bool = Field(default=False)
