from pydantic import BaseModel
from sqlmodel import Field

from gc_registry.organisation.schemas import OrganisationBase

# Organisation - corporate entities or individuals that represent trading bodies registered
# with the domain's regulatory business registration body (e.g. UK = Companies House)


class Organisation(OrganisationBase, table=True):
    id: int | None = Field(primary_key=True)
    # users: list[User] = Relationship(back_populates="organisation")


class OrganisationRead(OrganisationBase):
    id: int


class OrganisationUpdate(BaseModel):
    id: int
    name: str | None
    business_id: int | None
    website: str | None
    address: str | None
    primary_contact: str | None