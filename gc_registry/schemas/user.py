from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship

from gc_registry.models.user import UserBase
from gc_registry.schemas.user_account_link import UserAccountLink

if TYPE_CHECKING:
    from gc_registry.schemas.account import Account

# User - a single Organisation can have multiple Users, each with different roles and
# responsibilities at the discretion of the Organisation they are related to. Each
# User may be authorised to operate multiple accounts.


class User(UserBase, table=True):
    user_id: int = Field(primary_key=True, autoincrement=True)
    account_ids: Optional[List[int]] = Field(
        description="The accounts to which the user is registered.",
        sa_column=Column(ARRAY(String())),
    )
    accounts: Optional[List["Account"]] = Relationship(
        back_populates="users", link_model=UserAccountLink
    )


class UserRead(UserBase):
    user_id: int


class UserUpdate(UserBase):
    name: Optional[str]
    user_id: Optional[int]
    primary_contact: Optional[str]