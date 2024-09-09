import datetime

from sqlmodel import Field

from gc_registry import utils


class StorageActionBase(utils.ActiveRecord):
    """
    A record of a User's request to the registry to perform an action on an SCR/SDR.
    The registry must ensure that the User has the necessary authority to perform the requested action, and that the action is performed
    in accordance with the EnergyTag Standard and the registry's own policies and procedures.
    """

    action_response_status: str = Field(
        description="Specifies whether the requested action has been accepted or rejected by the registry."
    )
    source_id: int = Field(
        description="The Account ID of the Account within which the action shall occur or originate from.",
        foreign_key="account.id",
    )
    source_id: int = Field(
        description="The User that is performing the action, and can be verified as having the sufficient authority to perform the requested action on the Account specified.",
        foreign_key="user.id",
    )
    source_allocation_id: int | None = Field(
        description="The specific SCRs/SDRs onto which the action will be performed. Returns all records with the specified allocation ID."
    )
    action_request_datetime: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="The UTC datetime at which the User submitted the action to the registry.",
    )
    action_completed_datetime: datetime.datetime | None = Field(
        default_factory=datetime.datetime.now,
        description="The UTC datetime at which the registry confirmed to the User that their submitted action had either been successfully completed or rejected.",
    )
    charging_period_start: datetime.datetime | None = Field(
        description="The UTC datetime from which to filter records within the specified Account."
    )
    charging_period_end: datetime.datetime | None = Field(
        description="The UTC datetime up to which records within the specified Account are to be filtered."
    )
    storage_id: int | None = Field(
        description="Filter records associated with the specified production device."
    )
    storage_energy_source: str | None = Field(
        description="Filter records based on the fuel type used by the production Device.",
    )
    # TODO this also breaks pydantic validation, need to revisit
    # sparse_filter_list: dict[int, datetime.datetime] | None = Field(
    #     description="Overrides all other search criteria. Provide a list of Device ID - Datetime pairs to retrieve GC Bundles issued to each Device and datetime specified.",
    #     sa_column=Column(ARRAY(String())),
    # )
