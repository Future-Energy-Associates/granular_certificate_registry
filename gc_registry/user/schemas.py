import re

from pydantic import BaseModel, field_validator, model_serializer
from sqlmodel import Field

from gc_registry.account.schemas import AccountRead
from gc_registry.core.models.base import UserRoles


class UserBase(BaseModel):
    name: str
    email: str = Field(
        nullable=False,
        description="The email address of the User, used for authentication.",
    )
    role: UserRoles = Field(
        description="""The role of the User within the registry. A single User is assigned a role
                       by the Registry Administrator (which is itself a User for the purposes of managing allowable
                       actions), including: 'Admin', 'Audit User', 'Trading User',
                       and 'Production User'. The roles are used to determine the actions that the User is allowed
                       to perform within the registry, according to the EnergyTag Standard.""",
    )
    hashed_password: str | None = None
    is_deleted: bool = Field(default=False)

    @field_validator("email")
    def validate_email(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Please enter a valid email address.")
        return v


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    organisation: str | None = None
    hashed_password: str | None = None
    role: UserRoles | None = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: UserRoles
    accounts: list[AccountRead] | None = None
    organisation: str | None = None

    @model_serializer(mode="plain")
    def serializer(self, info, *, many=False):
        return {
            "role": self.role.name,
            "name": self.name,
            "email": self.email,
            "id": self.id,
            "accounts": [AccountRead.model_validate(a) for a in self.accounts]
            if self.accounts
            else None,
            "organisation": self.organisation,
        }
