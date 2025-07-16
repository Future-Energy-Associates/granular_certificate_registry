from pathlib import Path

import pandas as pd
import pytest

# Assuming these are available in your codebase
# from your_module import StorageRecord, FIFOStorageAllocator
# Define the StorageRecord Pydantic model
from gc_registry.storage.allocation.fifo import FIFOStorageAllocator
from gc_registry.storage.models import StorageRecord
from gc_registry.storage.schemas import StorageEfficiency


@pytest.fixture()
def storage_records() -> list[StorageRecord]:
    """
    Fixture to load storage records from a CSV file for testing.
    """
    # Load the CSV file into a DataFrame
    csv_path = Path(__file__).parent / "test_allocation_data.csv"
    df = pd.read_csv(csv_path)

    # parse the datetime columns
    df["flow_start_datetime"] = pd.to_datetime(
        df["flow_start_datetime"], errors="coerce"
    )
    df["flow_end_datetime"] = pd.to_datetime(df["flow_end_datetime"], errors="coerce")

    # check the sum if the 'flow_energy' for is_charging == True is greater than the sum for is_charging == False
    assert (
        df[df.is_charging]["flow_energy"].sum()
        > df[~df.is_charging]["flow_energy"].sum()
    ), "Total charging energy must be greater than total discharging energy."

    records = [StorageRecord.model_validate(row) for row in df.to_dict("records")]
    return records


@pytest.fixture()
def storage_efficiency() -> StorageEfficiency:
    """
    Fixture to provide a StorageEfficiency instance for testing.
    """
    return StorageEfficiency(
        efficiency_factor_methodology="Standard Methodology",
        efficiency_factor_interval_start=pd.Timestamp("2025-01-01T00:00:00Z"),
        efficiency_factor_interval_end=pd.Timestamp("2025-06-02T00:00:00Z"),
        storage_efficiency_factor=0.89,
    )


def test_fifo_allocation(
    storage_records: list[StorageRecord], storage_efficiency: StorageEfficiency
):
    allocator = FIFOStorageAllocator()
    allocator.allocate(storage_records, storage_efficiency)

    # validate the allocations
    allocator.validate_records()

    assert len(allocator.allocations) > 0, "No allocations were made."

    pd.DataFrame(allocator.allocations).to_csv(
        Path(__file__).parent / "fifo_allocations.csv", index=False
    )

    # Check that the sum of allocated energy matches the total energy in the records
    allocated_discharged_energy = sum(
        allocation["sdr_proportion"]
        * storage_records[allocation["sdr_allocation_id"]].flow_energy
        for allocation in allocator.allocations
    )
    allocated_charge_energy = sum(
        storage_records[allocation["scr_allocation_id"]].flow_energy
        for allocation in allocator.allocations
    )

    assert (
        allocated_discharged_energy <= allocated_charge_energy
    ), "Total discharge energy exceeds total charge energy adjusted for efficiency."
