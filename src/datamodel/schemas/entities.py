import datetime
import uuid as uuid_pkg
from typing import Optional
from typing import (
    AbstractSet,
    Any,
    Mapping,
    Sequence,
    Union,
)

from pydantic.fields import Undefined, UndefinedType
from pydantic.typing import NoArgAnyCallable
from sqlalchemy import ARRAY, Column, String

from sqlmodel import Field, Relationship

from energytag.datamodel.schemas import items, utils


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
    default: Any = Undefined,
    *args,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    exclude: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    include: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_mutation: bool = True,
    regex: Optional[str] = None,
    primary_key: bool = False,
    foreign_key: Optional[Any] = None,
    nullable: Union[bool, UndefinedType] = Undefined,
    index: Union[bool, UndefinedType] = Undefined,
    sa_column: Union[Column, UndefinedType] = Undefined,  # type: ignore
    sa_column_args: Union[Sequence[Any], UndefinedType] = Undefined,
    sa_column_kwargs: Union[Mapping[str, Any], UndefinedType] = Undefined,
    schema_extra: Optional[dict[str, Any]] = None,
    **kwargs
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
    website: Optional[str]
    address: Optional[str]


class Organisation(OrganisationBase, table=True):
    organisation_id: uuid_pkg.UUID = Field(
        primary_key=True, default_factory=uuid_pkg.uuid4
    )
    users: list["User"] = Relationship(back_populates="organisation")
    accounts: list["Account"] = Relationship(back_populates="organisation")


class OrganisationRead(OrganisationBase):
    organisation_id: uuid_pkg.UUID


class OrganisationUpdate(OrganisationBase):
    organisation_id: Optional[uuid_pkg.UUID]
    name: Optional[str]
    business_id: Optional[int]
    website: Optional[str]
    address: Optional[str]
    primary_contact: Optional[str]


# User - a single Organisation can have multiple Users, each with different roles and
# responsibilities at the discretion of the Organisation they are related to. Each
# User may be authorised to operate multiple accounts.


# a single user can be granted access to many accounts, and vice versa
class UserAccountLink(utils.ActiveRecord, table=True):
    user_id: Optional[uuid_pkg.UUID] = Field(
        default=None, foreign_key="user.user_id", primary_key=True
    )
    account_id: Optional[uuid_pkg.UUID] = Field(
        default=None, foreign_key="account.account_id", primary_key=True
    )


class UserBase(utils.ActiveRecord):
    name: str
    primary_contact: str
    organisation_id: items.ForeignOrganisationId = Field(
        foreign_key="organisation.organisation_id"
    )
    role: list[str] = Field(
        description="""The roles of the User with the registry. A single User can be assigned multiple roles
                       by the Registry Administrator (which is itself a User for the purposes of managing allowable
                       actions), including: 'GC Issuer', 'Production Registrar', 'Measurement Body', and 'Account Holder'.
                       The roles are used to determine the actions that the User is allowed to perform within the registry,
                       according to the EnergyTag Standard.""",
        sa_column=Column(ARRAY(String())),
    )


class User(UserBase, table=True):
    user_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    organisation: Organisation = Relationship(
        sa_relationship_kwargs={"cascade": "delete"}, back_populates="users"
    )
    accounts: list["Account"] = Relationship(
        back_populates="users", link_model=UserAccountLink
    )


class UserRead(UserBase):
    user_id: uuid_pkg.UUID


class UserUpdate(UserBase):
    name: Optional[str]
    user_id: Optional[uuid_pkg.UUID]
    primary_contact: Optional[str]
    account_id: Optional[uuid_pkg.UUID]


# Account - an Organisation can hold multiple accounts, into which
# certificates can be issued by the Issuing Body and managed by Users
# with the necessary authentication from their Organisation. Each
# account is linked to zero or more devices.


class AccountBase(utils.ActiveRecord):
    account_name: str
    organisation_id: items.ForeignOrganisationId = Field(
        foreign_key="organisation.organisation_id"
    )


class Account(AccountBase, table=True):
    account_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    organisation: Organisation = Relationship(
        sa_relationship_kwargs={"cascade": "delete"}, back_populates="accounts"
    )
    users: list["User"] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    devices: list["Device"] = Relationship(back_populates="devices")


class AccountRead(AccountBase):
    account_id: uuid_pkg.UUID
    organisation: Organisation
    users: list["User"]


class AccountUpdate(AccountBase):
    account_name: Optional[str]
    account_id: Optional[uuid_pkg.UUID]
    organisation: Optional[Organisation]
    user_id: Optional[uuid_pkg.UUID]


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
    location_id: uuid_pkg.UUID = Field(foreign_key="location.location_id", default=None)
    account_id: items.ForeignAccountId = Field(
        description="The account to which the device is registered, and into which GC Bundles will be issued for energy produced by this Device.",
        foreign_key="account.account_id",
    )


class Device(DeviceBase, table=True):
    device_id: uuid_pkg.UUID = Field(
        description="A unique identifier for the device. UUIDv4 could be used for this purpose, alternaties include the GS1 codes currently used under EECS.",
        primary_key=True,
        default_factory=uuid_pkg.uuid4,
    )
    location_of_device: Optional["Location"] = Relationship(back_populates="device")
    account: Account = Relationship(back_populates="devices")
    subsidy_support_ids: list["SubsidySupport"] = Relationship(
        sa_relationship_kwargs={"cascade": "delete"}, back_populates="device"
    )
    auxiliary_unit_ids: list["Device"] = Relationship(
        sa_relationship_kwargs={"cascade": "delete"}, back_populates="device"
    )
    image_ids: list["Image"] = Relationship(
        sa_relationship_kwargs={"cascade": "delete"}, back_populates="device"
    )
    meters: list["Meter"] = Relationship(
        sa_relationship_kwargs={"cascade": "delete"}, back_populates="device"
    )


class DeviceRead(DeviceBase):
    device_id: uuid_pkg.UUID


class DeviceUpdate(DeviceBase):
    device_id: Optional[uuid_pkg.UUID]
    device_name: Optional[str]
    account: Optional[Account]
    grid: Optional[str]
    energy_source: Optional[str]
    technology_type: Optional[str]
    operational_date: Optional[datetime.date]
    capacity: Optional[float]
    peak_demand: Optional[float]
    location_id: Optional[uuid_pkg.UUID]
    meter_id: Optional[uuid_pkg.UUID]


# Measurement Report
class MeasurementReportBase(utils.ActiveRecord):
    device_id: items.ForeignDeviceId = item_field(items.ForeignDeviceId)
    interval_start_datetime: items.IntervalStartDatetime = item_field(
        items.IntervalStartDatetime
    )
    interval_end_datetime: items.IntervalEndDatetime = item_field(
        items.IntervalEndDatetime
    )
    interval_usage: items.IntervalUsage = item_field(
        items.IntervalUsage,
        description="The quantity of energy consumed, produced, or stored in Wh by the device during the specified interval.",
    )
    gross_net_indicator: str = Field(
        description="Indicates whether the usage is gross or net of any losses in the system.",
    )


class MeasurementReport(MeasurementReportBase, table=True):
    measurement_report_id: uuid_pkg.UUID = Field(
        primary_key=True, default_factory=uuid_pkg.uuid4
    )


class MeasurementReportRead(MeasurementReportBase):
    measurement_report_id: uuid_pkg.UUID
    usage_units: items.valid_usage_units


class MeasurementReportUpdate(MeasurementReportBase):
    measurement_report_id: Optional[uuid_pkg.UUID]
    interval_start_datetime: Optional[items.IntervalStartDatetime]
    interval_end_datetime: Optional[items.IntervalEndDatetime]
    usage_units: Optional[items.valid_usage_units]


# Location
class LocationBase(utils.ActiveRecord):
    longitude: float
    latitude: float
    UPRN: Optional[int]
    postcode: Optional[str]
    building_name_number: Optional[str]
    street: Optional[str]
    city: Optional[str]
    county: Optional[str]


class Location(LocationBase, table=True):
    location_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    device: Optional["Device"] = Relationship(back_populates="location")


class LocationRead(LocationBase):
    location_id: uuid_pkg.UUID


class LocationUpdate(LocationBase):
    location_id: Optional[uuid_pkg.UUID]
    longitude: Optional[float]
    latitude: Optional[float]
    UPRN: Optional[int]
    postcode: Optional[str]
    building_name_number: Optional[str]
    street: Optional[str]
    city: Optional[str]
    county: Optional[str]


# Meter
class MeterBase(utils.ActiveRecord):
    type: Optional[str]
    serial: Optional[str]
    # mpan: Optional[int]
    # bmu: Optional[str]
    device_id: items.ForeignDeviceId = Field(
        foreign_key="device.device_id", default=None
    )


class Meter(MeterBase, table=True):
    meter_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)
    device: "Device" = Relationship(
        sa_relationship_kwargs={"cascade": "delete"}, back_populates="meters"
    )


class MeterRead(MeterBase):
    meter_id: uuid_pkg.UUID


class MeterUpdate(MeterBase):
    meter_id: Optional[uuid_pkg.UUID]
    type: Optional[str]
    serial: Optional[str]
    # mpan: Optional[int]


# Subsidy Support
class SubsidySupportBase(utils.ActiveRecord):
    scheme_name: str
    unit_rate: float
    device_id: Optional[uuid_pkg.UUID]
    support_start: datetime.date
    support_end: datetime.date


class SubsidySupport(SubsidySupportBase, table=True):
    subsidy_support_id: uuid_pkg.UUID = Field(
        primary_key=True, default_factory=uuid_pkg.uuid4
    )


class SubsidySupportRead(SubsidySupportBase):
    subsidy_support_id: uuid_pkg.UUID


class SubsidySupportUpdate(SubsidySupportBase):
    subsidy_support_id: Optional[uuid_pkg.UUID]
    scheme_name: Optional[str]
    unit_rate: Optional[float]
    device_id: Optional[uuid_pkg.UUID]
    support_start: Optional[datetime.date]
    support_end: Optional[datetime.date]


# Image
class ImageBase(utils.ActiveRecord):
    url: str
    name: str


class Image(ImageBase, table=True):
    image_id: uuid_pkg.UUID = Field(primary_key=True, default_factory=uuid_pkg.uuid4)


class ImageRead(ImageBase):
    image_id: uuid_pkg.UUID


class ImageUpdate(ImageBase):
    image_id: Optional[uuid_pkg.UUID]
    url: Optional[str]
    name: Optional[str]
