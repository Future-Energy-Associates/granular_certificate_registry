
from collections import deque

from gc_registry.storage.allocation.abstract import StorageAllocator
from gc_registry.storage.models import StorageRecord

from collections import deque

from gc_registry.storage.schemas import StorageEfficiency

class FIFOStorageAllocator(StorageAllocator):
    """
    FIFO Storage Allocator that allocates energy from storage records in a first-in-first-out manner.
    This allocator assumes that the storage records are ordered by their start time.
    It allocates energy from the oldest available storage record to the newest demand record.
    """
    @property
    def method(self) -> str:
        return "FIFO"
    
    def allocate(self, storage_charge_records: list[StorageRecord],storage_efficiency: StorageEfficiency):
        charge_queue = deque()
        self.allocations = []

        for record_orm in storage_charge_records:
            record = record_orm.model_dump()

            device_id = record["device_id"]
            is_charging = record["is_charging"]
            start_time = record["flow_start_datetime"]
            energy_wh = record["flow_energy"]
            record_id = record_orm.id

            if is_charging:
                # SCR
                charge_queue.append((
                    record_id,    
                    start_time,
                    energy_wh
                ))
            else:
                # SDR
                sdr_id = record_id
                sdr_energy = energy_wh
                gross_energy_needed = sdr_energy / storage_efficiency.storage_efficiency_factor

                while gross_energy_needed > 0.001 and charge_queue:
                    scr_id, scr_start, scr_available = charge_queue[0]
                    allocated = min(gross_energy_needed, scr_available)
                    sdr_proportion = round((allocated * storage_efficiency.storage_efficiency_factor) / sdr_energy, 6)
                    allocation={
                        "device_id": device_id,
                        "scr_allocation_id": scr_id,
                        "sdr_allocation_id": sdr_id,
                        "sdr_proportion": sdr_proportion,
                        "scr_allocation_methodology": self.method,
                        "gc_allocation_id": None,
                        "sdgc_allocation_id": None,
                    }

                    allocation.update(storage_efficiency.model_dump())

                    self.allocations.append(allocation)

                    gross_energy_needed -= allocated
                    remaining = scr_available - allocated

                    if remaining > 0.001:
                        charge_queue[0] = (scr_id, scr_start, remaining)
                    else:
                        charge_queue.popleft()


