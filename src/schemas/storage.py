import datetime
import uuid as uuid_pkg
from typing import Optional

from sqlmodel import Field

from src.schemas import utils


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
    gc_issuance_id: uuid_pkg.UUID = Field(
        description="The unique issuance ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    gc_bundle_id_range_start: int = Field(
        description="The start range ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    gc_bundle_id_range_end: int = Field(
        description="The end range ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    scr_geographic_matching_method: str = Field(
        description="Which type of geographic matching, as described in the EnergyTag GC Matching Standard, has been applied to allocated this SCR.",
    )
    sdr_allocation_id: Optional[uuid_pkg.UUID] = Field(
        description="When allocated, the unique ID of the Storage Discharge Record that has been allocated to this SCR. If blank, no SDR has been allocated to this SCR.",
        foreign_key="storagedischargerecord.sdr_allocation_id",
    )


class StorageChargeRecord(StorageChargeRecordBase, table=True):
    scr_allocation_id: uuid_pkg.UUID = Field(
        description="The unique ID of the Storage Charge Record that allocated the energy of the Storage Device to this SDR.",
        primary_key=True,
    )
    account_id: uuid_pkg.UUID = Field(
        foreign_key="account.account_id",
        description="Each SCR is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    device_id: uuid_pkg.UUID = Field(
        foreign_key="device.device_id",
        description="The Device ID of the Storage Device that is being charged.",
    )


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
    efficiency_factor_interval_start: Optional[datetime.datetime] = Field(
        description="""The UTC datetime from which the Storage Device calculates its effective efficiency factor for this SDR, based on total input and
                       output energy over the interval specified. This field describes only the method proposed in the EnergyTag Standard, and is not mandatory.""",
    )
    efficiency_factor_interval_end: Optional[datetime.datetime] = Field(
        description="The UTC datetime to which the Storage Device calculates its effective efficiency factor for this SDR.",
    )


class StorageDischargeRecord(StorageDischargeRecordBase, table=True):
    sdr_allocation_id: uuid_pkg.UUID = Field(
        description="The unique ID of this Storage Discharge Record.",
        primary_key=True,
    )
    device_id: uuid_pkg.UUID = Field(
        foreign_key="device.device_id",
        description="The Device ID of the Storage Device that is being charged.",
    )
    account_id: uuid_pkg.UUID = Field(
        foreign_key="account.account_id",
        description="Each SDR is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    scr_allocation_id: uuid_pkg.UUID = Field(
        description="The unique ID of the Storage Charge Record that allocated the energy charged into this Storage Device (adjusted for losses) to this SDR.",
        foreign_key="storagechargerecord.scr_allocation_id",
    )
