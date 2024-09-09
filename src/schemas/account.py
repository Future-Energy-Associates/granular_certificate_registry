import uuid as uuid_pkg
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from src.models.account import AccountBase
from src.schemas.user_account_link import UserAccountLink

if TYPE_CHECKING:
    from src.schemas.device import Device
    from src.schemas.user import User

# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.


class Account(AccountBase, table=True):
    account_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    users: List["User"] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    devices: List["Device"] = Relationship(back_populates="devices")


class AccountRead(AccountBase):
    account_id: uuid_pkg.UUID


class AccountUpdate(AccountBase):
    account_name: Optional[str]
    account_id: Optional[uuid_pkg.UUID]
