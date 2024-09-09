from typing import Optional

from src import utils


class OrganisationBase(utils.ActiveRecord):
    name: str
    business_id: int
    primary_contact: str
    website: Optional[str]
    address: Optional[str]
