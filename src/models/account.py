import uuid as uuid_pkg
from typing import List, Optional

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field

from src import utils


class AccountBase(utils.ActiveRecord):
    account_name: str
    user_ids: Optional[List[uuid_pkg.UUID]] = Field(
        description="The users registered to the account.",
        sa_column=Column(ARRAY(String())),
    )
