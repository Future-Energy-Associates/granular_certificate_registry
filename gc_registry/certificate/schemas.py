import datetime
from functools import partial

from pydantic import BaseModel, model_validator
from sqlalchemy import JSON, Column, Float
from sqlmodel import ARRAY, BigInteger, Field

from gc_registry.core.models.base import (
    CertificateActionType,
    CertificateStatus,
    EnergyCarrierType,
    EnergySourceType,
)

utc_datetime_now = partial(datetime.datetime.now, datetime.timezone.utc)

mutable_gc_attributes = [
    "certificate_status",
    "account_id",
    "sdr_allocation_id",
    "storage_efficiency_factor",
    "is_deleted",
    "bundle_id_range_start",
    "bundle_id_range_end",
]

certificate_query_param_map = {
    "source_id": "account_id",
    "certificate_period_start": None,
    "certificate_period_end": None,
    "device_id": "device_id",
    "energy_source": "energy_source",
    "certificate_status": "certificate_status",
}


class GranularCertificateBundleBase(BaseModel):
    """The GC Bundle is the primary unit of issuance and transfer within the EnergyTag standard, and only the Resgistry
    Administrator role can create, update, or withdraw GC Bundles.

    Requests to modify attributes including Account location, GC Bundle status, and Bundle splitting received from
    other Account holders should only be applied by the Registry administrator once all necessary validations have been
    performend.

    Validations and action execution are to be applied using a single queuing system, with changes made to the GC Bundle
    database applied with full ACID compliance. This ensures that all actions are applied in the order they are received,
    the state of the database is consistent at all times, and any errors can be rectified by reversing linearly through
    the queue.
    """

    issuance_id: str = Field(
        description="""A unique identifier assigned to the GC Bundle at the time of issuance.
        If the bundle is split through partial transfer or cancellation, this issuance ID
        remains unchanged across each child GC Bundle.""",
    )
    hash: str | None = Field(
        default=None,
        description="""A unique hash assigned to this bundle at the time of issuance,
        formed from the sha256 of the bundle's properties and, if the result of a bundle
        split, a nonce taken from the hash of the parent bundle.""",
    )

    ### Mutable Attributes ###
    certificate_status: CertificateStatus = Field(
        description="""One of: Active, Cancelled, Claimed, Expired, Withdrawn, Locked, Reserved."""
    )
    account_id: int = Field(
        foreign_key="account.id",
        description="Each GC Bundle is assigned to a single unique Account e.g. production Device account or trading account",
    )
    metadata_id: int = Field(
        foreign_key="issuancemetadata.id",
        description="Reference to the associated issuance metadata",
    )
    bundle_id_range_start: int = Field(
        sa_column=Column(BigInteger()),
        description="""The individual Granular Certificates within this GC Bundle, each representing a
                        contant volume of energy, generated within the production start and end time interval,
                        is issued an ID in a format that can be represented sequentially and in a
                        clearly ascending manner, displayed on the GC Bundle instance by start and end IDs indicating the minimum
                        and maximum IDs contained within the Bundle, inclusive of both range end points and all integers
                        within that range.""",
    )
    bundle_id_range_end: int = Field(
        sa_column=Column(BigInteger()),
        description="""The start and end range IDs of GC Bundles may change as they are split and transferred between Accounts,
                       or partially cancelled.""",
    )
    bundle_quantity: int = Field(
        description="""The quantity of Granular Certificates within this GC Bundle, according to a
                        standardised energy volume per Granular Certificate, rounded down to the nearest Wh. Equal to
                        (bundle_id_range_end - bundle_id_range_start + 1)."""
    )

    ### Bundle Characteristics ###
    energy_carrier: EnergyCarrierType = Field(
        description="The form of energy that the GC Bundle represents, for example: Electricity, Hydrogen, Ammonia.",
    )
    energy_source: EnergySourceType = Field(
        description="The fuel type used to generate the energy represented by the GC Bundle, for example: Solar, Wind, Biomass, Nuclear, Coal, Gas, Oil, Hydro.",
    )
    face_value: int = Field(
        description="States the quantity of energy in Watt-hours (Wh) represented by each Granular Certificate within this GC Bundle.",
    )
    issuance_post_energy_carrier_conversion: bool = Field(
        description="Indicate whether this GC Bundle have been issued following an energy conversion event, for example in a power to hydrogen facility.",
    )

    ### Other Optional Characteristics ###
    emissions_factor_production_device: float | None = Field(
        default=None,
        description="May indicate the emissions factor (kgCO2e/MWh) of the production Device at the datetime in which this GC Bundle was issued against.",
    )  # :TODO: Look at marginal emissions factor on metadata definition - could this be moved to EmissionsFactor table?
    emissions_factor_source: str | None = Field(
        default=None,
        description="Includes a reference to the calculation methodology of the production Device emissions factor.",
    )

    ### Production Device Characteristics ###
    device_id: int = Field(
        foreign_key="device.id",
        description="Each GC Bundle is associated with a single production Device.",
    )

    ### Temporal Characteristics ###
    production_starting_interval: datetime.datetime = Field(
        description="""The datetime in UTC format indicating the start of the relevant production period.
                        GC Bundles shall be issued over a maximum production period of one hour,
                        under the assumption that the certificates represent an even distribution of power generation within that period.""",
    )
    production_ending_interval: datetime.datetime = Field(
        description="The datetime in UTC format indicating the end of the relevant production period.",
    )
    expiry_datestamp: datetime.datetime = Field(
        description="The date in UTC format (YYYY-MM-DD) indicating the point at which the GC Bundle will be rendered invalid if they have not been cancelled. This expiry period can vary across Domains.",
    )

    ### Storage Characteristics ###
    is_storage: int = Field(
        description="Indicates whether the Device ID is associated with a storage Device.",
    )
    sdr_allocation_id: int | None = Field(
        default=None,
        description="The unique ID of the Storage Discharge Record that has been allocated to this GC Bundle.",
        foreign_key="storagedischargerecord.sdr_allocation_id",
    )
    storage_efficiency_factor: float | None = Field(
        default=None,
        description="The efficiency factor of the storage Device that has discharged the energy represented by this GC Bundle.",
    )
    is_deleted: bool = Field(default=False)


class GranularCertificateBundleCreate(GranularCertificateBundleBase):
    hash: str | None = None


class IssuanceMetaDataBase(BaseModel):
    """
    Attributes that detail the Issuing Body characteristics and legal status of the GC Bundle.
    """

    ### Issuing Body Characteristics ###
    country_of_issuance: str = Field(
        description="The Domain under which the Issuing Body of this GC Bundle has authority to issue.",
    )
    connected_grid_identification: str = Field(
        description="A Domain-specific identifier indicating the infrastructure into which the energy has been injected.",
    )
    issuing_body: str = Field(
        description="The Issuing Body that has issued this GC Bundle.",
    )
    legal_status: str | None = Field(
        default=None,
        description="May contain pertinent information on the Issuing Authority, where relevant.",
    )
    issuance_purpose: str | None = Field(
        default=None,
        description="May contain the purpose of the GC Bundle issuance, for example: Disclosure, Subsidy Support.",
    )
    support_received: str | None = Field(
        default=None,
        description="May contain information on any support received for the generation or investment into the production Device for which this GC Bundle have been issued.",
    )
    quality_scheme_reference: str | None = Field(
        default=None,
        description="May contain any references to quality schemes for which this GC Bundle were issued.",
    )
    dissemination_level: str | None = Field(
        default=None,
        description="Specifies whether the energy associated with this GC Bundle was self-consumed or injected into a private or public grid.",
    )
    issue_market_zone: str = Field(
        description="References the bidding zone and/or market authority and/or price node within which the GC Bundle have been issued.",
    )


class GranularCertificateBundleRead(BaseModel):
    """The GC Bundle is the primary unit of issuance and transfer within the EnergyTag standard, and only the Resgistry
    Administrator role can create, update, or withdraw GC Bundles.

    Requests to modify attributes including Account location, GC Bundle status, and Bundle splitting received from
    other Account holders should only be applied by the Registry administrator once all necessary validations have been
    performend.

    Validations and action execution are to be applied using a single queuing system, with changes made to the GC Bundle
    database applied with full ACID compliance. This ensures that all actions are applied in the order they are received,
    the state of the database is consistent at all times, and any errors can be rectified by reversing linearly through
    the queue.
    """

    ### Mutable Attributes ###
    certificate_status: CertificateStatus = Field(
        description="""One of: Active, Cancelled, Claimed, Expired, Withdrawn, Locked, Reserved."""
    )
    account_id: int = Field(
        foreign_key="account.id",
        description="Each GC Bundle is issued to a single unique production Account that its production Device is individually registered to.",
    )
    bundle_id_range_start: int = Field(
        description="""The individual Granular Certificates within this GC Bundle, each representing a
                        contant volume of energy, generated within the production start and end time interval,
                        is issued an ID in a format that can be represented sequentially and in a
                        clearly ascending manner, displayed on the GC Bundle instance by start and end IDs indicating the minimum
                        and maximum IDs contained within the Bundle, inclusive of both range end points and all integers
                        within that range.""",
    )
    bundle_id_range_end: int = Field(
        description="""The start and end range IDs of GC Bundles may change as they are split and transferred between Accounts,
                       or partially cancelled.""",
    )
    bundle_quantity: int = Field(
        description="""The quantity of Granular Certificates within this GC Bundle, according to a
                        standardised energy volume per Granular Certificate, rounded down to the nearest Wh. Equal to
                        (bundle_id_range_end - bundle_id_range_start + 1)."""
    )

    ### Bundle Characteristics ###
    issuance_id: str = Field(
        description="""A unique identifier assigned to the GC Bundle at the time of issuance.
        If the bundle is split through partial transfer or cancellation, this issuance ID
        remains unchanged across each child GC Bundle.""",
    )
    energy_carrier: str = Field(
        description="The form of energy that the GC Bundle represents, for example: Electricity, Hydrogen, Ammonia. In the current version of the standard (v2), this field is always Electricity.",
    )
    energy_source: str = Field(
        description="The fuel type used to generate the energy represented by the GC Bundle, for example: Solar, Wind, Biomass, Nuclear, Coal, Gas, Oil, Hydro.",
    )
    face_value: int = Field(
        description="States the quantity of energy in Watt-hours (Wh) represented by each Granular Certificate within this GC Bundle.",
    )
    issuance_post_energy_carrier_conversion: bool = Field(
        description="Indicate whether this GC Bundle have been issued following an energy conversion event, for example in a power to hydrogen facility.",
    )
    registry_configuration: int = Field(
        default=1,
        description="""The configuration of the Registry that issued this GC Bundle; either 1, 2, or 3 at the time of writing (Standard v2). Enables tracking of related certificates
                        to aid auditing and error detection""",
    )

    ### Production Device Characteristics ###
    device_id: int = Field(
        foreign_key="device.id",
        description="Each GC Bundle is associated with a single production Device.",
    )
    device_name: str = Field(description="The name of the production Device.")
    device_technology_type: str = Field(
        description="The Device's technology type, for example: Offshore Wind Turbine, Biomass Plant, Fixed Hydro.",
    )
    device_production_start_date: datetime.datetime = Field(
        description="The date on which the production Device began generating energy.",
    )
    device_capacity: int = Field(
        description="The maximum capacity of the production Device in Watts (W).",
    )
    device_location: tuple[float, float] = Field(
        description="The GPS coordinates of the production or Storage Device responsible for releasing the energy represented by the GC Bundle.",
        sa_column=Column(ARRAY(Float)),
    )
    device_type: str = Field(
        description="Whether the GC Bundle represents energy that has been generated by a production Device or released by a storage unit.",
    )

    ### Temporal Characteristics ###
    production_starting_interval: datetime.datetime = Field(
        description="""The datetime in UTC format indicating the start of the relevant production period.
                        GC Bundles shall be issued over a maximum production period of one hour,
                        under the assumption that the certificates represent an even distribution of power generation within that period.""",
    )
    production_ending_interval: datetime.datetime = Field(
        description="The datetime in UTC format indicating the end of the relevant production period.",
    )
    expiry_datestamp: datetime.datetime = Field(
        description="The date in UTC format (YYYY-MM-DD) indicating the point at which the GC Bundle will be rendered invalid if they have not been cancelled. This expiry period can vary across Domains.",
    )

    ### Storage Characteristics ###
    is_storage: bool = Field(
        description="Indicates whether the Device ID is associated with a storage Device.",
    )
    sdr_allocation_id: int | None = Field(
        default=None,
        description="The unique ID of the Storage Discharge Record that has been allocated to this GC Bundle.",
        foreign_key="storagedischargerecord.sdr_allocation_id",
    )
    discharging_start_datetime: datetime.datetime | None = Field(
        default=None,
        description="The UTC datetime at which the Storage Device began discharging the energy represented by this SD-GC (inherited from the allocated SDR).",
    )
    discharging_end_datetime: datetime.datetime | None = Field(
        default=None,
        description="The UTC datetime at which the Storage Device ceased discharging energy represented by this SD-GC (inherited from the allocated SDR).",
    )
    storage_efficiency_factor: float | None = Field(
        default=None,
        description="The efficiency factor of the storage Device that has discharged the energy represented by this GC Bundle.",
    )

    ### Issuing Body Characteristics ###
    country_of_issuance: str = Field(
        description="The Domain under which the Issuing Body of this GC Bundle has authority to issue.",
    )
    connected_grid_identification: str = Field(
        description="A Domain-specific identifier indicating the infrastructure into which the energy has been injected.",
    )
    issuing_body: str = Field(
        description="The Issuing Body that has issued this GC Bundle.",
    )
    legal_status: str | None = Field(
        default=None,
        description="May contain pertinent information on the Issuing Authority, where relevant.",
    )
    issuance_purpose: str | None = Field(
        default=None,
        description="May contain the purpose of the GC Bundle issuance, for example: Disclosure, Subsidy Support.",
    )
    support_received: str | None = Field(
        default=None,
        description="May contain information on any support received for the generation or investment into the production Device for which this GC Bundle have been issued.",
    )
    quality_scheme_reference: str | None = Field(
        default=None,
        description="May contain any references to quality schemes for which this GC Bundle were issued.",
    )
    dissemination_level: str | None = Field(
        default=None,
        description="Specifies whether the energy associated with this GC Bundle was self-consumed or injected into a private or public grid.",
    )
    issue_market_zone: str = Field(
        description="References the bidding zone and/or market authority and/or price node within which the GC Bundle have been issued.",
    )

    ### Other Optional Characteristics ###
    emissions_factor_production_device: float | None = Field(
        default=None,
        description="May indicate the emissions factor (kgCO2e/MWh) of the production Device at the datetime in which this GC Bundle was issued against.",
    )
    emissions_factor_source: str | None = Field(
        default=None,
        description="Includes a reference to the calculation methodology of the production Device emissions factor.",
    )
    hash: str = Field(
        default=None,
        description="""A unique hash assigned to this bundle at the time of issuance,
        formed from the sha256 of the bundle's properties and, if the result of a bundle
        split, a nonce taken from the hash of the parent bundle.""",
    )
    is_deleted: bool = Field(default=False)


class GranularCertificateActionBase(BaseModel):
    source_id: int = Field(
        description="The Account ID of the Account within which the action shall occur or originate from."
    )
    user_id: int = Field(
        description="The User that is performing the action, and can be verified as having the sufficient authority to perform the requested action on the Account specified."
    )
    granular_certificate_bundle_ids: list[int] = Field(
        sa_column=Column(JSON),
        description="The specific GC Bundle(s) onto which the action will be performed. Returns all GC Bundles with the specified issuance ID.",
    )
    certificate_quantity: int | None = Field(
        default=None,
        description="""Overrides GC Bundle range start and end IDs, if specified.
        Returns the specified number of certificates from a given GC bundle to action on,
        splitting from the start of the range.""",
    )
    certificate_bundle_percentage: float | None = Field(
        default=None,
        gt=0,
        le=1,
        description="""Overrides GC Bundle range start and end IDs, if specified.
        The percentage from 0 to 100 of the identified GC bundle to action on, splitting from
        the start of the range and rounding down to the nearest Wh.""",
    )
    localise_time: bool = Field(
        default=True,
        description="Indicates whether the request should be localised to the Account's timezone.",
    )


class GranularCertificateQuery(BaseModel):
    source_id: int = Field(
        description="The Account ID of the Account within which the action shall occur or originate from."
    )
    user_id: int = Field(
        description="The User that is performing the action, and can be verified as having the sufficient authority to perform the requested action on the Account specified."
    )
    localise_time: bool = Field(
        default=True,
        description="Indicates whether the request should be localised to the Account's timezone.",
    )
    issuance_ids: list[str] | None = Field(
        default=None,
        description="The specific GC Bundle(s) onto which the action will be performed. Returns all GC Bundles with the specified issuance ID.",
    )
    device_id: int | None = Field(
        default=None,
        description="Filter GC Bundles associated with the specified production device.",
    )
    energy_source: str | None = Field(
        default=None,
        description="Filter GC Bundles based on the fuel type used by the production Device.",
    )
    certificate_period_start: datetime.datetime | None = Field(
        default=None,
        description="""The UTC datetime from which to filter GC Bundles within the specified Account.
        If provided without certificate_period_end, returns all GC Bundles from the specified datetime to the present.""",
    )
    certificate_period_end: datetime.datetime | None = Field(
        default=None,
        description="""The UTC datetime up to which GC Bundles within the specified Account are to be filtered.
        If provided without certificate_period_start, returns all GC Bundles up to the specified datetime.""",
    )
    certificate_status: CertificateStatus | None = Field(
        default=None, description="""Filter on the status of the GC Bundles."""
    )

    @model_validator(mode="after")
    def validate_date_range(cls, values):
        start = values.certificate_period_start
        end = values.certificate_period_end
        if start and end and start >= end:
            raise ValueError(
                "certificate_period_end must be greater than certificate_period_start."
            )
        return values


class GranularCertificateTransfer(GranularCertificateActionBase):
    action_type: CertificateActionType = Field(
        default=CertificateActionType.TRANSFER,
        const=True,
    )
    target_id: int = Field(
        description="For (recurring) transfers, the Account ID into which the GC Bundles are to be transferred to.",
    )

    @model_validator(mode="before")
    def ensure_action_type_is_not_set(cls, values):
        if "action_type" in values:
            raise ValueError("`action_type` cannot be set explicitly.")
        return values


class GranularCertificateCancel(GranularCertificateActionBase):
    action_type: CertificateActionType = Field(
        default=CertificateActionType.CANCEL,
        const=True,
    )
    beneficiary: str | None = Field(
        default=None,
        description="The Beneficiary entity that may make a claim on the attributes of the cancelled GC Bundles. If not specified, the Account holder is treated as the Beneficiary.",
    )

    @model_validator(mode="before")
    def ensure_action_type_is_not_set(cls, values):
        if "action_type" in values:
            raise ValueError("`action_type` cannot be set explicitly.")
        return values


class GranularCertificateReserve(GranularCertificateActionBase):
    action_type: CertificateActionType = Field(
        default=CertificateActionType.RESERVE,
        const=True,
    )
    target_id: int = Field(
        description="For (recurring) transfers, the Account ID into which the GC Bundles are to be transferred to.",
    )

    @model_validator(mode="before")
    def ensure_action_type_is_not_set(cls, values):
        if "action_type" in values:
            raise ValueError("`action_type` cannot be set explicitly.")
        return values


class GranularCertificateClaim(GranularCertificateActionBase):
    action_type: CertificateActionType = Field(
        default=CertificateActionType.CLAIM,
        const=True,
    )
    beneficiary: str = Field(
        default=None,
        description="The Beneficiary entity that may make a claim on the attributes of the cancelled GC Bundles. If not specified, the Account holder is treated as the Beneficiary.",
    )
    target_id: int = Field(
        description="For (recurring) transfers, the Account ID into which the GC Bundles are to be transferred to.",
    )

    @model_validator(mode="before")
    def ensure_action_type_is_not_set(cls, values):
        if "action_type" in values:
            raise ValueError("`action_type` cannot be set explicitly.")
        return values


class GranularCertificateWithdraw(GranularCertificateActionBase):
    action_type: CertificateActionType = Field(
        default=CertificateActionType.WITHDRAW,
        const=True,
    )

    @model_validator(mode="before")
    def ensure_action_type_is_not_set(cls, values):
        if "action_type" in values:
            raise ValueError("`action_type` cannot be set explicitly.")
        return values


class GranularCertificateLock(GranularCertificateActionBase):
    action_type: CertificateActionType = Field(
        default=CertificateActionType.LOCK,
        const=True,
    )

    @model_validator(mode="before")
    def ensure_action_type_is_not_set(cls, values):
        if "action_type" in values:
            raise ValueError("`action_type` cannot be set explicitly.")
        return values


class GranularCertificateActionRead(GranularCertificateActionBase):
    id: int | None = Field(
        primary_key=True,
        description="A unique ID assigned to this action.",
    )
