from typing import List

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field

from gc_registry import utils


class UserBase(utils.ActiveRecord):
    name: str
    primary_contact: str
    roles: List[str] = Field(
        description="""The roles of the User with the registry. A single User can be assigned multiple roles
                       by the Registry Administrator (which is itself a User for the purposes of managing allowable
                       actions), including: 'GC Issuer', 'Production Registrar', 'Measurement Body', and 'Trading User',
                       and 'Production User'. The roles are used to determine the actions that the User is allowed
                       to perform within the registry, according to the EnergyTag Standard.""",
        sa_column=Column(ARRAY(String())),
    )
