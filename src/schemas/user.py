import uuid as uuid_pkg
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship

from src.models.user import UserBase
from src.schemas.user_account_link import UserAccountLink

if TYPE_CHECKING:
    from src.schemas.account import Account

# User - a single Organisation can have multiple Users, each with different roles and
# responsibilities at the discretion of the Organisation they are related to. Each
# User may be authorised to operate multiple accounts.


class User(UserBase, table=True):
    user_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    account_ids: Optional[List[uuid_pkg.UUID]] = Field(
        description="The accounts to which the user is registered.",
        sa_column=Column(ARRAY(String())),
    )
    accounts: Optional[List["Account"]] = Relationship(
        back_populates="users", link_model=UserAccountLink
    )


class UserRead(UserBase):
    user_id: uuid_pkg.UUID


class UserUpdate(UserBase):
    name: Optional[str]
    user_id: Optional[uuid_pkg.UUID]
    primary_contact: Optional[str]
