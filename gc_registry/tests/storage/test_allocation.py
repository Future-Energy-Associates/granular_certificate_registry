import pandas as pd
from datetime import datetime
from pathlib import Path

# Assuming these are available in your codebase
# from your_module import StorageRecord, FIFOStorageAllocator

# Define the StorageRecord Pydantic model
from pydantic import BaseModel
import pytest

from gc_registry.storage.allocation.fifo import FIFOStorageAllocator
from gc_registry.storage.models import StorageRecord

@pytest.fixture()
def storage_records() -> list[StorageRecord]:
    """
    Fixture to load storage records from a CSV file for testing.
    """
    # Load the CSV file into a DataFrame
    csv_path = Path(__file__).parent / "test_allocation_data.csv"
    df = pd.read_csv(csv_path)
    column_mapping = {
         "hour":"flow_start_datetime",	
         "charged (Wh)":"charged",
        "discharged (Wh)": "discharged",
        "SOC (Wh)":"soc",
    }
    df.rename(columns=column_mapping, inplace=True)
    df['flow_start_datetime'] = pd.to_datetime(df['flow_start_datetime'].str.strip(" America/Denver"))
    df['flow_end_datetime'] = df['flow_start_datetime'] + pd.Timedelta(hours=1)

    df['is_charging'] = df['charged'] > 0
    df['flow_energy'] = df.apply(
        lambda row: row['charged'] if row['is_charging'] else row['discharged'], axis=1
    )
    df.index.name = 'id'
    df.reset_index(inplace=True)
    df['device_id'] = 1

    records = [StorageRecord.model_validate(row) for row in df.to_dict('records')]
    return records

def test_fifo_allocation(storage_records: list[StorageRecord]):

    allocator = FIFOStorageAllocator(efficiency=0.87)
    allocator.allocate(storage_records)

    # validate the allocations
    allocator.validate_records()

    assert len(allocator.allocations) > 0, "No allocations were made."

    pd.DataFrame(allocator.allocations).to_csv(
        Path(__file__).parent / "fifo_allocations.csv", index=False
    )

    # Check that the sum of allocated energy matches the total energy in the records
    allocated_discharged_energy = sum(
        allocation['sdr_proportion'] * storage_records[allocation['sdr_allocation_id']].flow_energy
        for allocation in allocator.allocations
    )
    allocated_charge_energy = sum(
        storage_records[allocation['scr_allocation_id']].flow_energy
        for allocation in allocator.allocations
    )


    assert allocated_discharged_energy <= allocated_charge_energy, "Total discharge energy exceeds total charge energy adjusted for efficiency."
