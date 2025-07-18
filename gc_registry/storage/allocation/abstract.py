from abc import ABC, abstractmethod
from typing import Any

from gc_registry.device.models import Device
from gc_registry.logging_config import logger
from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord
from gc_registry.storage.schemas import StorageEfficiency


def get_storage_record_from_allocation_id(
    storage_charge_records: list[StorageRecord], allocation_id: int
) -> StorageRecord | None:
    """
    Retrieve a StorageRecord from a list of storage charge records based on the allocation ID.
    """
    for record in storage_charge_records:
        if record.id == allocation_id:
            return record
    return None


class StorageAllocator(ABC):
    """
    Abstract base class for energy storage allocators.
    """

    def __init__(self, device: Device, storage_efficiency: StorageEfficiency):
        self.raw_allocations: list[dict[str, Any]] = []
        self.allocations: list[AllocatedStorageRecord] = []
        self.efficiency = storage_efficiency
        self.device = device

    @property
    @abstractmethod
    def method(self) -> str:
        """Returns the name of the allocation method (e.g., FIFO, LIFO)."""
        pass

    @abstractmethod
    def allocate(
        self,
        storage_charge_records: list[StorageRecord],
    ):
        """
        Perform the allocation given a list of storage charge records and the storage efficiency.
        This method should be implemented by subclasses to define the specific allocation logic.
        """
        pass

    def export_energy_validation(
        self,
        validated_records: list[AllocatedStorageRecord],
        storage_charge_records: list[StorageRecord],
    ) -> bool:
        """
        # check that the sum of all exported energy between each allocation is less than the device's capacity * efficiency
        # 1. for each allocation record get the start and end time
        # 2. filter the storage charge records to get the energy exported between those times
        # 3. sum the exported energy and check against the device's capacity * efficiency
        """
        for record in validated_records:
            scr = get_storage_record_from_allocation_id(
                storage_charge_records, record.scr_allocation_id
            )
            if not scr:
                raise ValueError(
                    f"SCR with allocation ID {record.scr_allocation_id} not found."
                )
            sdr = get_storage_record_from_allocation_id(
                storage_charge_records, record.sdr_allocation_id
            )
            if not sdr:
                raise ValueError(
                    f"SDR with allocation ID {record.sdr_allocation_id} not found."
                )

            # get all the storage records with flow_start_datetime > scr.flow_start_datetime and flow_start_datetime < sdr.flow_start_datetime
            exported_energy = sum(
                record.flow_energy
                for record in storage_charge_records
                if scr.flow_start_datetime
                < record.flow_start_datetime
                < sdr.flow_start_datetime
                and not record.is_charging
            )

            if (
                exported_energy
                > self.device.capacity * self.efficiency.storage_efficiency_factor
            ):
                err = (
                    f"Exported energy {exported_energy} between SCR {scr.id} and SDR {sdr.id} "
                    f"exceeds device capacity {self.device.capacity} * efficiency factor {self.efficiency.storage_efficiency_factor}."
                )
                logger.error(err)
                return False

        return True

    def validate_records(
        self, storage_charge_records: list[StorageRecord]
    ) -> list[AllocatedStorageRecord] | None:
        """
        Validate the records to ensure they are suitable for allocation.
        """
        if not self.raw_allocations:
            err = "No records provided for allocation."
            logger.error(err)
            return None

        for record in self.raw_allocations:
            allocated_storage_record = AllocatedStorageRecord.model_validate(record)
            self.allocations.append(allocated_storage_record)
        if not self.allocations:
            raise ValueError("No valid records found for allocation.")

        self.export_energy_validation(self.allocations, storage_charge_records)

        return self.allocations
