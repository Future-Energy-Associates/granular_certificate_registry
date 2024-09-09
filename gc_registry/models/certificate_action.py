import datetime

from sqlmodel import Field

from gc_registry import utils


class GranularCertificateActionBase(utils.ActiveRecord):
    # TODO validate with an enum at the class definition level
    action_type: str = Field(
        description="The type of action to be performed on the GC Bundle.",
    )
    source_id: int = Field(
        description="The Account ID of the Account within which the action shall occur or originate from."
    )
    source_id: int = Field(
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
    # TODO this currently can't pass Pydantic validation, need to revisit
    # sparse_filter_list: Tuple[str, str] | None = Field(
    #     description="Overrides all other search criteria. Provide a list of Device ID - Datetime pairs to retrieve GC Bundles issued to each Device and datetime specified.",
    #     sa_column=Column(ARRAY(String(), String())),
    # )
