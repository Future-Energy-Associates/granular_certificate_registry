from typing import List, Optional

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field

from gc_registry import utils


class AccountBase(utils.ActiveRecord):
    account_name: str
    user_ids: Optional[List[int]] = Field(
        description="The users registered to the account.",
        sa_column=Column(ARRAY(String())),
    )
