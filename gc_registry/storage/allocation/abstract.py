from abc import ABC, abstractmethod

from gc_registry.logging_config import logger
from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord
from gc_registry.storage.schemas import StorageEfficiency


class StorageAllocator(ABC):
    """
    Abstract base class for energy storage allocators.
    """

    def __init__(self):
        self.allocations = []

    @property
    @abstractmethod
    def method(self) -> str:
        """Returns the name of the allocation method (e.g., FIFO, LIFO)."""
        pass

    def set_efficiency(self, efficiency: float):
        """
        Set the round-trip efficiency of the storage system.
        """
        if not (0 < efficiency <= 1):
            raise ValueError("Efficiency must be between 0 and 1.")
        self.efficiency = efficiency

    @abstractmethod
    def allocate(
        self,
        storage_charge_records: list[StorageRecord],
        storage_efficiency: StorageEfficiency,
    ):
        """
        Perform the allocation given a list of storage charge records and the storage efficiency.
        This method should be implemented by subclasses to define the specific allocation logic.
        """
        pass

    def validate_records(self) -> list[AllocatedStorageRecord] | None:
        """
        Validate the records to ensure they are suitable for allocation.
        """
        if not self.allocations:
            err = "No records provided for allocation."
            logger.error(err)
            return None

        validated_records = []
        for record in self.allocations:
            allocated_storage_record = AllocatedStorageRecord.model_validate(record)
            validated_records.append(allocated_storage_record)
        if not validated_records:
            raise ValueError("No valid records found for allocation.")

        return validated_records
