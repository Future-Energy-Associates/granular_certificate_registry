import datetime
from enum import Enum
from typing import Union

from pydantic import BaseModel
from sqlmodel import Field

from gc_registry import utils


class FlowType(str, Enum):
    CHARGING = "charging"
    DISCHARGING = "discharging"


class StorageRecordBase(utils.ActiveRecord):
    device_id: int = Field(
        description="The Device ID of the Storage Device that is being charged or discharged.",
        foreign_key="device.id",
    )
    is_charging: bool = Field(
        description="Specifies whether the Storage Device is being charged or discharged.",
    )
    flow_start_datetime: datetime.datetime = Field(
        description="The UTC datetime at which the Storage Device began charging or discharging energy.",
    )
    flow_end_datetime: datetime.datetime = Field(
        description="The UTC datetime at which the Storage Device ceased charging or discharging energy.",
    )
    flow_energy: float = Field(
        description="The quantity of energy in Watt-hours (Wh) that the Storage Device has charged or discharged.",
    )
    validator_id: int | None = Field(
        description="An optional ID provided by the Storage Validator party to reference this Storage Charge/Discharge Record.",
    )


class AllocatedStorageRecordBase(utils.ActiveRecord):
    device_id: int = Field(
        description="The Device ID of the Storage Device that is being charged or discharged.",
        foreign_key="device.id",
    )
    scr_allocation_id: int = Field(
        description="The unique ID of the SCR that has been allocated to this matched record.",
        foreign_key="storagerecord.id",
    )
    sdr_allocation_id: int = Field(
        description="The unique ID of the SDR that has been allocated to this matched record.",
        foreign_key="storagerecord.id",
    )
    sdr_proportion: float = Field(
        description="The proportion of the SDR that has been allocated to the linked SCR",
        gt=0.0,
        le=1.0,
    )
    scr_allocation_methodology: str = Field(
        description="The method by which the energy of the Storage Device was allocated to this SCR/SDR, for example: FIFO, LIFO, weighted average, or Storage Operator's discretion.",
    )
    gc_allocation_id: int | None = Field(
        description="The unique ID of the cancelled GC Bundle that has been allocated to this matched record.",
        foreign_key="granularcertificatebundle.id",
    )
    sdgc_allocation_id: int | None = Field(
        description="The unique ID of the SD-GC Bundle that has been issued against this matched record.",
        foreign_key="granularcertificatebundle.id",
    )
    efficiency_factor_methodology: str = Field(
        description="The method by which the energy storage losses of the Storage Device were calculated.",
    )
    efficiency_factor_interval_start: datetime.datetime = Field(
        description="""The UTC datetime from which the Storage Device calculates its effective efficiency factor for this SCR/SDR, based on total input and
                       output energy over the interval specified. This field describes only the method proposed in the EnergyTag Standard, and is not mandatory.""",
    )
    efficiency_factor_interval_end: datetime.datetime = Field(
        description="The UTC datetime to which the Storage Device calculates its effective efficiency factor for this SCR/SDR.",
    )
    storage_efficiency_factor: float = Field(
        description="The efficiency factor of the Storage Device applied to this SCR/SDR.",
        ge=0.0,
        le=1.0,
    )


class AllocatedStorageRecordCreate(AllocatedStorageRecordBase):
    pass


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
    is_deleted: bool = Field(default=False)


class StorageActionResponse(StorageActionBase):
    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class StorageRecordQueryResponse(StorageActionResponse):
    filtered_records: Union[list[StorageRecordBase], None]


class AllocatedStorageRecordQueryResponse(StorageActionResponse):
    filtered_records: Union[list[AllocatedStorageRecordBase], None]


class StorageRecordSubmissionResponse(BaseModel):
    total_charge_energy: float
    total_discharge_energy: float
    total_energy: float
    total_records: int
    message: str


class AllocatedStorageRecordSubmissionResponse(BaseModel):
    total_records: int
    message: str
