from typing import (
    Optional,
)

from sqlmodel import Field, Relationship

from gc_registry.models.organisation import OrganisationBase
from gc_registry.schemas import user

# Organisation - corporate entities or individuals that represent trading bodies registered
# with the domain's regulatory business registration body (e.g. UK = Companies House)


class Organisation(OrganisationBase, table=True):
    organisation_id: int = Field(primary_key=True, autoincrement=True)
    users: list[user.User] = Relationship(back_populates="organisation")


class OrganisationRead(OrganisationBase):
    organisation_id: int


class OrganisationUpdate(OrganisationBase):
    organisation_id: Optional[int]
    name: Optional[str]
    business_id: Optional[int]
    website: Optional[str]
    address: Optional[str]
    primary_contact: Optional[str]
