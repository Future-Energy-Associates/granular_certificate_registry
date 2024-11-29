import datetime
from typing import Union

from sqlmodel import Field

from gc_registry import utils


class StorageChargeRecordBase(utils.ActiveRecord):
    charging_start_datetime: datetime.datetime = Field(
        description="The UTC datetime at which the Storage Device began charging energy.",
    )
    charging_end_datetime: datetime.datetime = Field(
        description="The UTC datetime at which the Storage Device ceased charging energy.",
    )
    charging_energy: int = Field(
        description="The quantity of energy in Watt-hours (Wh) that the Storage Device has been charged with.",
    )
    charging_energy_source: str = Field(
        description="""The energy source from which the Storage Device was charged, matching the energy source of the GC Bundles
                       that were cancelled and allocated to the Storage Device.""",
    )
    gc_issuance_id: int = Field(
        description="The unique issuance ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    granular_certificate_bundle_id_range_start: int = Field(
        description="The start range ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    granular_certificate_bundle_id_range_end: int = Field(
        description="The end range ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    scr_geographic_matching_method: str = Field(
        description="Which type of geographic matching, as described in the EnergyTag GC Matching Standard, has been applied to allocated this SCR.",
    )
    sdr_allocation_id: int | None = Field(
        description="When allocated, the unique ID of the Storage Discharge Record that has been allocated to this SCR. If blank, no SDR has been allocated to this SCR.",
        foreign_key="storagedischargerecord.sdr_allocation_id",
    )
    is_deleted: bool = Field(default=False)


class StorageDischargeRecordBase(utils.ActiveRecord):
    discharging_start_datetime: datetime.datetime = Field(
        description="The UTC datetime at which the Storage Device began discharging energy.",
    )
    discharging_end_datetime: datetime.datetime = Field(
        description="The UTC datetime at which the Storage Device ceased discharging energy.",
    )
    discharge_energy: float = Field(
        description="The quantity of energy in Watt-hours (Wh) that the Storage Device has discharged.",
    )
    charging_energy_source: str = Field(
        description="""The energy source from which the Storage Device was charged, matching the energy source of the GC Bundles
                       that were cancelled and allocated to the Storage Device.""",
    )
    scr_allocation_methodology: str = Field(
        description="The method by which the energy of the Storage Device was allocated to this SDR, for example: FIFO, LIFO, weighted average, or Storage Operator's discretion.",
    )
    efficiency_factor_methodology: str = Field(
        description="The method by which the energy storage losses of the Storage Device were calculated.",
    )
    efficiency_factor_interval_start: datetime.datetime | None = Field(
        description="""The UTC datetime from which the Storage Device calculates its effective efficiency factor for this SDR, based on total input and
                       output energy over the interval specified. This field describes only the method proposed in the EnergyTag Standard, and is not mandatory.""",
    )
    efficiency_factor_interval_end: datetime.datetime | None = Field(
        description="The UTC datetime to which the Storage Device calculates its effective efficiency factor for this SDR.",
    )
    is_deleted: bool = Field(default=False)


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
    user_id: int = Field(
        description="The User that is performing the action, and can be verified as having the sufficient authority to perform the requested action on the Account specified.",
        foreign_key="registry_user.id",
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
    is_deleted: bool = Field(default=False)
    # TODO this also breaks pydantic validation, need to revisit
    # sparse_filter_list: dict[int, datetime.datetime] | None = Field(
    #     description="Overrides all other search criteria. Provide a list of Device ID - Datetime pairs to retrieve GC Bundles issued to each Device and datetime specified.",
    #     sa_column=Column(ARRAY(String())),
    # )


class StorageActionResponse(StorageActionBase):
    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class SCRQueryResponse(StorageActionResponse):
    filtered_scrs: Union[list[StorageChargeRecordBase], None]


class SDRQueryResponse(StorageActionResponse):
    filtered_sdrs: Union[list[StorageDischargeRecordBase], None]
