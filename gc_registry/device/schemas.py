import datetime

from pydantic import model_validator
from sqlmodel import Field

from gc_registry import utils
from gc_registry.core.models.base import DeviceTechnologyType, EnergySourceType


class DeviceBase(utils.ActiveRecord):
    device_name: str = Field(
        description="The name assigned to the device by the operator/owner of the device.",
        min_length=1,
        max_length=255,
    )
    local_device_identifier: str | None = Field(
        default=None,
        description="""A unique identifier for the device, ideally used by the juristiction's grid
                       operator to identify the device and link it to available data sources. This
                       could be a meter number, a serial number, or other appropriate identifier""",
        unique=True,
        index=True,
    )
    grid: str = Field(
        description="The controlling authority of the grid that the device is connected to",
        min_length=1,
        max_length=255,
    )
    energy_source: EnergySourceType = Field(
        description="The type of energy source that the device uses to generate or store electricity.",
    )
    technology_type: DeviceTechnologyType = Field(
        description="The technology category of the device.",
    )
    operational_date: datetime.datetime = Field(
        description="The date that the device became operational.",
    )
    power_mw: float = Field(
        description="The maximum power output of the device in MW.",
        ge=0,
    )
    peak_demand: float = Field(
        description="The peak self-consumption of the device in MW.",
        ge=0,
    )
    location: str = Field(
        description="The location of the device, rendered as an address or a lon/lat pair.",
        min_length=1,
        max_length=255,
    )
    energy_mwh: float | None = Field(
        default=None,
        description="""If relevant, the total energy capacity of the device in MWh.
                       For storage devices, this is the product of power_mw
                       and the duration of the device in hours.""",
        ge=0,
    )
    is_storage: bool = Field(
        default=False,
        description="Whether the device is a storage device.",
    )

    @model_validator(mode="after")
    def validate_energy_mwh(self):
        if (self.is_storage is True) and (self.energy_mwh is None):
            raise ValueError("Energy capacity is required for battery storage devices")
        return self
