from sqlmodel import Field

from gc_registry import utils


class OrganisationBase(utils.ActiveRecord):
    name: str
    business_id: int
    primary_contact: str
    website: str | None
    address: str | None
    is_deleted: bool = Field(default=False)
