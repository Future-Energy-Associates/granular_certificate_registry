import datetime

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
    gc_bundle_id_range_start: int = Field(
        description="The start range ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    gc_bundle_id_range_end: int = Field(
        description="The end range ID of the GC Bundle that was cancelled and allocated to this SCR.",
    )
    scr_geographic_matching_method: str = Field(
        description="Which type of geographic matching, as described in the EnergyTag GC Matching Standard, has been applied to allocated this SCR.",
    )
    sdr_allocation_id: int | None = Field(
        description="When allocated, the unique ID of the Storage Discharge Record that has been allocated to this SCR. If blank, no SDR has been allocated to this SCR.",
        foreign_key="storagedischargerecord.sdr_allocation_id",
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
    efficiency_factor_interval_start: datetime.datetime | None = Field(
        description="""The UTC datetime from which the Storage Device calculates its effective efficiency factor for this SDR, based on total input and
                       output energy over the interval specified. This field describes only the method proposed in the EnergyTag Standard, and is not mandatory.""",
    )
    efficiency_factor_interval_end: datetime.datetime | None = Field(
        description="The UTC datetime to which the Storage Device calculates its effective efficiency factor for this SDR.",
    )
