import datetime
from typing import (
    AbstractSet,
    Any,
    List,
    Mapping,
    Sequence,
    Union,
)

from pydantic import BaseModel
from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship

from gc_registry.datamodel.schemas import utils

field_attrs = [
    "default",
    "default_factory",
    "alias",
    "title",
    "description",
    "include",
    "const",
    "gt",
    "ge",
    "lt",
    "le",
    "multiple_of",
    "min_items",
    "max_items",
    "min_length",
    "max_length",
    "allow_mutation",
    "regex",
    "primary_key",
    "foreign_key",
    "nullable",
    "index",
    "sa_column",
    "sa_column_args",
    "sa_column_kwargs",
    "schema_extra",
]


def item_field(
    item,
    default: Any = None,
    *args,
    default_factory: Any | None = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclude: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    include: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    const: bool | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    allow_mutation: bool = True,
    regex: str | None = None,
    primary_key: bool = False,
    foreign_key: Any | None = None,
    nullable: Union[bool, Any] = None,
    index: Union[bool, Any] = None,
    sa_column: Union[Column, Any] = None,  # type: ignore
    sa_column_args: Union[Sequence[Any], Any] = None,
    sa_column_kwargs: Union[Mapping[str, Any], Any] = None,
    schema_extra: dict[str, Any] | None = None,
    **kwargs,
):
    # Everything apart from the item is optional
    # First do a hasattr pass and add if so
    # Then work through anything passed as a param
    locals_ = locals()
    kwargs = {}

    for attr in field_attrs:
        if hasattr(item, attr):
            kwargs.update({attr: getattr(item, attr)})

        if hasattr(locals_, attr):
            kwargs.update({attr: getattr(locals_, attr)})

    field = Field(*args, **kwargs)

    return field


### Entities work on a linear hierarchical structure:
### Organisation -> User -> Account -> Device -> Meter


# Organisation - corporate entities or individuals that represent trading bodies registered
# with the domain's regulatory business registration body (e.g. UK = Companies House)
class OrganisationBase(utils.ActiveRecord):
    name: str
    business_id: int
    primary_contact: str
    website: str | None
    address: str | None


class Organisation(OrganisationBase, table=True):
    id: int | None = Field(primary_key=True)
    users: list["User"] = Relationship(back_populates="organisation")


class OrganisationRead(OrganisationBase):
    id: int


class OrganisationUpdate(BaseModel):
    id: int
    name: str | None
    business_id: int | None
    website: str | None
    address: str | None
    primary_contact: str | None


# User - a single Organisation can have multiple Users, each with different roles and
# responsibilities at the discretion of the Organisation they are related to. Each
# User may be authorised to operate multiple accounts.


# a single user can be granted access to many accounts, and vice versa
class UserAccountLink(utils.ActiveRecord, table=True):
    user_id: int = Field(default=None, foreign_key="user.user_id", primary_key=True)
    account_id: int = Field(
        default=None, foreign_key="account.account_id", primary_key=True
    )


class UserBase(utils.ActiveRecord):
    name: str
    primary_contact: str
    role: List[str] = Field(
        description="""The roles of the User with the registry. A single User can be assigned multiple roles
                       by the Registry Administrator (which is itself a User for the purposes of managing allowable
                       actions), including: 'GC Issuer', 'Production Registrar', 'Measurement Body', and 'Trading User',
                       and 'Production User'. The roles are used to determine the actions that the User is allowed
                       to perform within the registry, according to the EnergyTag Standard.""",
        sa_column=Column(ARRAY(String())),
    )
    organisation_id: int = Field(foreign_key="organisation.organisation_id")


class User(UserBase, table=True):
    id: int | None = Field(primary_key=True)
    account_ids: list[int] = Field(
        description="The accounts to which the user is registered.",
        sa_column=Column(ARRAY(String())),
    )
    accounts: list["Account"] | None = Relationship(
        back_populates="users", link_model=UserAccountLink
    )


class UserRead(UserBase):
    id: int


class UserUpdate(BaseModel):
    id: int
    name: str | None
    primary_contact: str | None


# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.


class AccountBase(utils.ActiveRecord):
    account_name: str


class Account(AccountBase, table=True):
    id: int | None = Field(primary_key=True)
    users: list["User"] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    devices: list["Device"] = Relationship(back_populates="devices")


class AccountRead(AccountBase):
    id: int
    users: list["User"]


class AccountUpdate(BaseModel):
    id: int | None
    account_name: str | None


# Device - production, consumption, or storage, each device is associated
# with exactly one account owned by an organisation operating in the same
# domain as the Device.


class DeviceBase(utils.ActiveRecord):
    device_name: str
    grid: str
    energy_source: str
    technology_type: str
    operational_date: datetime.date
    capacity: float
    peak_demand: float
    location: str
    account_id: int = Field(
        description="The account to which the device is registered, and into which GC Bundles will be issued for energy produced by this Device.",
        foreign_key="account.account_id",
    )


class Device(DeviceBase, table=True):
    id: int | None = Field(
        description="A unique identifier for the device. Integer has been used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
    )
    account: Account = Relationship(back_populates="devices")


class DeviceRead(DeviceBase):
    id: int


class DeviceUpdate(BaseModel):
    id: int
    account: Account | None
    grid: str | None
    energy_source: str | None
    technology_type: str | None
    operational_date: datetime.date | None
    capacity: float | None
    peak_demand: float | None
    location: str | None


# Measurement Report
class MeasurementReportBase(utils.ActiveRecord):
    device_id: int
    interval_start_datetime: datetime.datetime
    interval_end_datetime: datetime.datetime
    interval_usage: int = Field(
        description="The quantity of energy consumed, produced, or stored in Wh by the device during the specified interval.",
    )
    gross_net_indicator: str = Field(
        description="Indicates whether the usage is gross or net of any losses in the system.",
    )


class MeasurementReport(MeasurementReportBase, table=True):
    measurement_report_id: int | None = Field(primary_key=True)


class MeasurementReportRead(MeasurementReportBase):
    measurement_report_id: int


class MeasurementReportUpdate(BaseModel):
    measurement_report_id: int
    interval_start_datetime: datetime.datetime | None
    interval_end_datetime: datetime.datetime | None
