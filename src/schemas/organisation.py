import uuid as uuid_pkg
from typing import (
    Optional,
)

from sqlmodel import Field, Relationship

from src.models.organisation import OrganisationBase
from src.schemas import user

# Organisation - corporate entities or individuals that represent trading bodies registered
# with the domain's regulatory business registration body (e.g. UK = Companies House)


class Organisation(OrganisationBase, table=True):
    organisation_id: uuid_pkg.UUID = Field(
        primary_key=True, default_factory=uuid_pkg.uuid4
    )
    users: list[user.User] = Relationship(back_populates="organisation")


class OrganisationRead(OrganisationBase):
    organisation_id: uuid_pkg.UUID


class OrganisationUpdate(OrganisationBase):
    organisation_id: Optional[uuid_pkg.UUID]
    name: Optional[str]
    business_id: Optional[int]
    website: Optional[str]
    address: Optional[str]
    primary_contact: Optional[str]
