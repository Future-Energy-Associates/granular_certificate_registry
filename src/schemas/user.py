import uuid as uuid_pkg
from typing import (
    List,
    Optional,
)

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship

from src.schemas import utils

# User - a single Organisation can have multiple Users, each with different roles and
# responsibilities at the discretion of the Organisation they are related to. Each
# User may be authorised to operate multiple accounts.


class UserAccountLink(utils.ActiveRecord, table=True):
    user_id: Optional[uuid_pkg.UUID] = Field(
        default=None, foreign_key="user.user_id", primary_key=True
    )
    account_id: Optional[uuid_pkg.UUID] = Field(
        default=None, foreign_key="account.account_id", primary_key=True
    )


class UserBase(utils.ActiveRecord):
    name: str
    primary_contact: str
    role: List[str] = Field(
        description="""The roles of the User with the registry. A single User can be assigned multiple roles
                       by the Registry Administrator (which is itself a User for the purposes of managing allowable
                       actions), including: 'GC Issuer', 'Production Registrar', 'Measurement Body', and 'Trading User',
                       and 'Production User'. The roles are used to determine the actions that the User is allowed
                       to perform within the registry, according to the EnergyTag Standard.""",
        sa_column=Column(ARRAY(String())),
    )
    organisation_id: uuid_pkg.UUID = Field(foreign_key="organisation.organisation_id")


class User(UserBase, table=True):
    user_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    account_ids: Optional[List[uuid_pkg.UUID]] = Field(
        description="The accounts to which the user is registered.",
        sa_column=Column(ARRAY(String())),
    )
    accounts: Optional[list["Account"]] = Relationship(
        back_populates="users", link_model=UserAccountLink
    )


class UserRead(UserBase):
    user_id: uuid_pkg.UUID


class UserUpdate(UserBase):
    name: Optional[str]
    user_id: Optional[uuid_pkg.UUID]
    primary_contact: Optional[str]
