from pydantic import BaseModel
from sqlalchemy import ARRAY, Column, Integer
from sqlmodel import Field

from gc_registry import utils


class AccountBase(utils.ActiveRecord):
    account_name: str
    user_ids: list[int | None] = Field(
        default=[],
        description="The users registered to the account.",
        sa_column=Column(ARRAY(Integer())),
    )
    is_deleted: bool = Field(default=False)


class AccountUpdate(BaseModel):
    account_name: str | None = None
    user_ids: list[int] | None = None


class AccountWhitelist(BaseModel):
    add_to_whitelist: list[int] | None = None
    remove_from_whitelist: list[int] | None = None


class AccountSummary(BaseModel):
    id: int
    account_name: str
    num_devices: int
    num_devices_by_type: dict[str, int] | None = None
    device_capacity_by_type: dict[str, int] | None = None
    num_granular_certificate_bundles: int
    num_cancelled_granular_certificate_bundles: int
    total_certificate_energy: int
    energy_by_fuel_type: dict[str, int] | None = None


class AccountRead(BaseModel):
    id: int
    account_name: str
    user_ids: list[int] | None = None
