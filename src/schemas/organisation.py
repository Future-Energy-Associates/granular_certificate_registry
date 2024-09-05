import uuid as uuid_pkg
from typing import (
    Optional,
)

from sqlmodel import Field, Relationship

from src.schemas import utils


# Organisation - corporate entities or individuals that represent trading bodies registered
# with the domain's regulatory business registration body (e.g. UK = Companies House)
class OrganisationBase(utils.ActiveRecord):
    name: str
    business_id: int
    primary_contact: str
    website: Optional[str]
    address: Optional[str]


class Organisation(OrganisationBase, table=True):
    organisation_id: uuid_pkg.UUID = Field(
        primary_key=True, default_factory=uuid_pkg.uuid4
    )
    users: list["User"] = Relationship(back_populates="organisation")


class OrganisationRead(OrganisationBase):
    organisation_id: uuid_pkg.UUID


class OrganisationUpdate(OrganisationBase):
    organisation_id: Optional[uuid_pkg.UUID]
    name: Optional[str]
    business_id: Optional[int]
    website: Optional[str]
    address: Optional[str]
    primary_contact: Optional[str]
