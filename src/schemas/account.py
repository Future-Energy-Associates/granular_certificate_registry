import uuid as uuid_pkg
from typing import ForwardRef, List, Optional

from sqlmodel import Field, Relationship

from src.models.account import AccountBase
from src.schemas.user_account_link import UserAccountLink

# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.

User = ForwardRef("User", module="src.schemas.user")
Device = ForwardRef("Device", module="src.schemas.device")


class Account(AccountBase, table=True):
    account_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    users: List[User] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    devices: List[Device] = Relationship(back_populates="devices")


Account.model_rebuild()


class AccountRead(AccountBase):
    account_id: uuid_pkg.UUID
    users: list[User]


AccountRead.model_rebuild()


class AccountUpdate(AccountBase):
    account_name: Optional[str]
    account_id: Optional[uuid_pkg.UUID]
