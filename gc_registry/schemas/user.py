from typing import TYPE_CHECKING, List

from pydantic import BaseModel
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
    id: int = Field(primary_key=True)
    account_ids: List[int] | None = Field(
        description="The accounts to which the user is registered.",
        sa_column=Column(ARRAY(String())),
    )
    accounts: List["Account"] | None = Relationship(
        back_populates="users", link_model=UserAccountLink
    )


class UserRead(UserBase):
    id: int


class UserUpdate(BaseModel):
    id: int
    name: str | None
    primary_contact: str | None
