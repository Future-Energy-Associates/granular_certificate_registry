import datetime
import uuid

from sqlalchemy import Column, Float
from sqlmodel import ARRAY, Field

from gc_registry import utils


class GranularCertificateBundleBase(utils.ActiveRecord):
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

    issuance_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="""A unique identifier assigned to the GC Bundle at the time of issuance.
        If the bundle is split through partial transfer or cancellation, this issuance ID
        remains unchanged across each child GC Bundle.""",
    )

    ### Mutable Attributes ###
    certificate_status: str = Field(
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
    issuance_datestamp: datetime.datetime = Field(
        description="The date in UTC format (YYYY-MM-DD) indicating the date on which the Issuing Body delivered the GC Bundle to the production Device's registered Account.",
    )
    expiry_datestamp: datetime.datetime = Field(
        description="The date in UTC format (YYYY-MM-DD) indicating the point at which the GC Bundle will be rendered invalid if they have not been cancelled. This expiry period can vary across Domains.",
    )

    ### Storage Characteristics ###
    storage_id: int | None = Field(
        default=None,
        foreign_key="device.id",
        description="The Device ID of the storage Device that released the energy represented by the GC Bundle.",
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
    storage_device_location: tuple[float, float] | None = Field(
        default=None,
        description="The GPS coordinates of the storage Device that has discharged the energy represented by this GC Bundle.",
        sa_column=Column(ARRAY(Float)),
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


class GranularCertificateActionBase(utils.ActiveRecord):
    # TODO validate with an enum at the class definition level
    action_type: str = Field(
        description="The type of action to be performed on the GC Bundle.",
    )
    source_id: int = Field(
        description="The Account ID of the Account within which the action shall occur or originate from."
    )
    user_id: int = Field(
        description="The User that is performing the action, and can be verified as having the sufficient authority to perform the requested action on the Account specified."
    )
    target_id: int | None = Field(
        description="For (recurring) transfers, the Account ID into which the GC Bundles are to be transferred to."
    )
    source_certificate_issuance_id: int | None = Field(
        description="The specific GC Bundle(s) onto which the action will be performed. Returns all GC Bundles with the specified issuance ID."
    )
    source_certificate_bundle_id_range_start: int | None = Field(
        description="If an issuance ID is specified, returns a GC Bundle containing all certificates between and inclusive of the range start and end IDs provided.",
    )
    source_certificate_bundle_id_range_end: int | None = Field(
        description="If an issuance ID is specified, returns a GC Bundle containing all certificates between and inclusive of the range start and end IDs provided.",
    )
    action_request_datetime: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="The UTC datetime at which the User submitted the action to the registry.",
    )
    action_completed_datetime: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="The UTC datetime at which the registry confirmed to the User that their submitted action had either been successfully completed or rejected.",
    )
    initial_action_datetime: datetime.datetime | None = Field(
        description="If recurring, the UTC datetime of the first action that is to be completed.",
    )
    recurring_action_period_units: str | None = Field(
        description="If recurring, the unit of time described by the recurring_action_period_quantity field, for example: 'days', 'weeks', 'months', 'years'."
    )
    recurring_action_period_quantity: int | None = Field(
        description="If recurring, the number of units of time (specified by the units field) between each action."
    )
    number_of_recurring_actions: int | None = Field(
        description="If recurring, including the first action, the number of recurring actions to perform before halting the recurring action."
    )
    beneficiary: str | None = Field(
        description="The Beneficiary entity that may make a claim on the attributes of the cancelled GC Bundles. If not specified, the Account holder is treated as the Beneficiary."
    )
    certificate_period_start: datetime.datetime | None = Field(
        description="The UTC datetime from which to filter GC Bundles within the specified Account."
    )
    certificate_period_end: datetime.datetime | None = Field(
        description="The UTC datetime up to which GC Bundles within the specified Account are to be filtered."
    )
    certificate_quantity: int | None = Field(
        description="""Overrides GC Bundle range start and end IDs, if specified.
        Of the GC Bundles identified, return the total number of certificates to action on,
        splitting GC Bundles from the start of the range where necessary.""",
    )
    id: int | None = Field(
        description="Filter GC Bundles associated with the specified production device."
    )
    energy_source: str | None = Field(
        description="Filter GC Bundles based on the fuel type used by the production Device.",
    )
    certificate_status: str | None = Field(
        description="""Filter on the status of the GC Bundles."""
    )
    id_to_update_to: int | None = Field(
        description="Update the associated Account of a GC Bundle."
    )
    certificate_status_to_update_to: str | None = Field(
        description="Update the status of a GC Bundle."
    )
    is_deleted: bool = Field(default=False)
    # TODO this currently can't pass Pydantic validation, need to revisit
    # sparse_filter_list: Tuple[str, str] | None = Field(
    #     description="Overrides all other search criteria. Provide a list of Device ID - Datetime pairs to retrieve GC Bundles issued to each Device and datetime specified.",
    #     sa_column=Column(ARRAY(String(), String())),
    # )
