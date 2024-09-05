import datetime
import uuid as uuid_pkg
from typing import List, Optional, Union

from sqlmodel import Field

from src.schemas import certificate, utils

# A Transfer object is specified by a User, and is stored in a transaction table that
# lists all transfers and cancellations between accounts for audit purposes

# "transfer", "recurring_transfer", "cancel", "claim", "withdraw"


class GranularCertificateActionBase(utils.ActiveRecord):
    # TODO validate with an enum at the class definition level
    action_type: str = Field(
        description="The type of action to be performed on the GC Bundle.",
    )
    source_account_id: uuid_pkg.UUID = Field(
        description="The Account ID of the Account within which the action shall occur or originate from."
    )
    source_user_id: uuid_pkg.UUID = Field(
        description="The User that is performing the action, and can be verified as having the sufficient authority to perform the requested action on the Account specified."
    )
    target_account_id: Optional[uuid_pkg.UUID] = Field(
        description="For (recurring) transfers, the Account ID into which the GC Bundles are to be transferred to."
    )
    source_certificate_issuance_id: Optional[uuid_pkg.UUID] = Field(
        description="The specific GC Bundle(s) onto which the action will be performed. Returns all GC Bundles with the specified issuance ID."
    )
    source_certificate_bundle_id_range_start: Optional[int] = Field(
        description="If an issuance ID is specified, returns a GC Bundle containing all certificates between and inclusive of the range start and end IDs provided.",
    )
    source_certificate_bundle_id_range_end: Optional[int] = Field(
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
    initial_action_datetime: Optional[datetime.datetime] = Field(
        description="If recurring, the UTC datetime of the first action that is to be completed.",
    )
    recurring_action_period_units: Optional[str] = Field(
        description="If recurring, the unit of time described by the recurring_action_period_quantity field, for example: 'days', 'weeks', 'months', 'years'."
    )
    recurring_action_period_quantity: Optional[int] = Field(
        description="If recurring, the number of units of time (specified by the units field) between each action."
    )
    number_of_recurring_actions: Optional[int] = Field(
        description="If recurring, including the first action, the number of recurring actions to perform before halting the recurring action."
    )
    beneficiary: Optional[str] = Field(
        description="The Beneficiary entity that may make a claim on the attributes of the cancelled GC Bundles. If not specified, the Account holder is treated as the Beneficiary."
    )
    certificate_period_start: Optional[datetime.datetime] = Field(
        description="The UTC datetime from which to filter GC Bundles within the specified Account."
    )
    certificate_period_end: Optional[datetime.datetime] = Field(
        description="The UTC datetime up to which GC Bundles within the specified Account are to be filtered."
    )
    certificate_quantity: Optional[int] = Field(
        description="""Overrides GC Bundle range start and end IDs, if specified.
        Of the GC Bundles identified, return the total number of certificates to action on,
        splitting GC Bundles from the start of the range where necessary.""",
    )
    device_id: Optional[uuid_pkg.UUID] = Field(
        description="Filter GC Bundles associated with the specified production device."
    )
    energy_source: Optional[str] = Field(
        description="Filter GC Bundles based on the fuel type used by the production Device.",
    )
    certificate_status: Optional[str] = Field(
        description="""Filter on the status of the GC Bundles."""
    )
    account_id_to_update_to: Optional[uuid_pkg.UUID] = Field(
        description="Update the associated Account of a GC Bundle."
    )
    certificate_status_to_update_to: Optional[str] = Field(
        description="Update the status of a GC Bundle."
    )
    # TODO this currently can't pass Pydantic validation, need to revisit
    # sparse_filter_list: Optional[Tuple[str, str]] = Field(
    #     description="Overrides all other search criteria. Provide a list of Device ID - Datetime pairs to retrieve GC Bundles issued to each Device and datetime specified.",
    #     sa_column=Column(ARRAY(String(), String())),
    # )


class GranularCertificateAction(GranularCertificateActionBase, table=True):
    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class GranularCertificateActionResponse(GranularCertificateActionBase):
    action_response_status: str = Field(
        description="Specifies whether the requested action has been accepted or rejected by the registry."
    )


class GranularCertificateQueryResponse(GranularCertificateActionResponse):
    filtered_certificate_bundles: Union[
        List[certificate.GranularCertificateBundle], None
    ]
