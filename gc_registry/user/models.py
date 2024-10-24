from typing import TYPE_CHECKING, List

from pydantic import BaseModel
from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship

from gc_registry import utils
from gc_registry.user.schemas import UserBase

if TYPE_CHECKING:
    from gc_registry.account.models import Account

# Each User may be authorised to operate multiple accounts.


class UserAccountLink(utils.ActiveRecord, table=True):
    user_id: int | None = Field(
        default=None, foreign_key="registry_user.id", primary_key=True
    )
    account_id: int | None = Field(
        default=None, foreign_key="account.id", primary_key=True
    )
    is_deleted: bool = Field(default=False)


class User(UserBase, table=True):
    # Postgres reserves the name "user" as a keyword, so we use "registry_user" instead
    __tablename__: str = "registry_user"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    account_ids: List[int] | None = Field(
        default=None,
        description="The accounts to which the user is registered.",
        sa_column=Column(ARRAY(String())),
    )
    accounts: List["Account"] | None = Relationship(
        back_populates="users", link_model=UserAccountLink
    )
    organisation: str | None = Field(
        default=None,
        description="The organisation to which the user is registered.",
    )


class UserRead(UserBase):
    id: int


class UserUpdate(BaseModel):
    name: str | None = None
    primary_contact: str | None = None
    roles: List[str] | None = None
    account_ids: List[int] | None = None
    organisation: str | None = None
