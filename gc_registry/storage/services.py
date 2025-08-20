import datetime
from typing import Any, Hashable, cast

import pandas as pd
from esdbclient import EventStoreDBClient
from fastapi import Depends
from sqlmodel import Session, SQLModel, func, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.core.database import db, events
from gc_registry.core.models.base import (
    CertificateStatus,
    EnergyCarrierType,
    EnergySourceType,
)
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.models import Device
from gc_registry.settings import settings
from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord
from gc_registry.storage.validation import (
    validate_allocated_records,
    validate_allocated_records_against_gc_bundles,
)


def create_charge_records_from_metering_data(
    storage_records_df: pd.DataFrame,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> dict:
    """Create a Storage Charge Record from the specified metering data."""

    storage_records_df["is_charging"] = storage_records_df["flow_energy"] < 0
    storage_records_df["flow_energy"] = storage_records_df["flow_energy"].abs()

    # Create the storage records
    created_storage_records = StorageRecord.create(
        storage_records_df.to_dict(orient="records"),
        write_session,
        read_session,
        esdb_client,
    )

    created_storage_records_cast = cast(list[StorageRecord], created_storage_records)

    # Calculate summary values
    total_charge_energy = storage_records_df[storage_records_df["is_charging"]][
        "flow_energy"
    ].sum()

    total_discharge_energy = storage_records_df[~storage_records_df["is_charging"]][
        "flow_energy"
    ].sum()

    total_energy = storage_records_df["flow_energy"].sum()
    total_records = len(storage_records_df)

    return {
        "total_charge_energy": total_charge_energy,
        "total_discharge_energy": total_discharge_energy,
        "total_energy": total_energy,
        "total_records": total_records,
        "record_ids": [record.id for record in created_storage_records_cast],
        "message": "Storage records created successfully.",
    }


def create_allocated_storage_records_from_submitted_data(
    allocated_storage_records_df: pd.DataFrame,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> list[AllocatedStorageRecord] | None:
    """Storage Validator Only: Create a list of Allocated Storage Records from the specified submitted data.

    Relies on there being existing validated Storage Charge/Discharge Records for the specified device that include
    validator IDs to match the Allocated Storage Records against.
    """

    # Validate that existing Storage Charge/Discharge Records exist for each allocation entry
    device_ids = allocated_storage_records_df["device_id"].unique()
    if len(device_ids) != 1:
        raise ValueError(
            "Only one device ID is supported for Allocated Storage Record creation."
        )
    device_id = int(device_ids[0])

    # Retrieve all validator storage record IDs for the device
    validator_storage_record_ids = StorageRecord.validator_ids_by_device_id(
        device_id,
        read_session,
    )

    # Retrieve storage records referenced by the validator IDs in the allocation record submission
    validator_storage_records = StorageRecord.by_validator_ids(
        validator_storage_record_ids,
        read_session,
    )
    validator_storage_records_df = pd.DataFrame(
        [record.model_dump() for record in validator_storage_records]
    )

    # Assert that the referenced GC bundle IDs exist and have been cancelled
    allocated_storage_records_df["gc_allocation_id"] = [
        int(id) if id != "" else None
        for id in allocated_storage_records_df["gc_allocation_id"]
    ]
    allocated_storage_records_df["sdgc_allocation_id"] = [
        int(id) if id != "" else None
        for id in allocated_storage_records_df["sdgc_allocation_id"]
    ]
    gc_bundle_ids = allocated_storage_records_df["gc_allocation_id"].dropna().unique()

    # If no allocation IDs are provided, skip for now
    if len(gc_bundle_ids) != 0:
        gc_bundles_ids_in_db = read_session.exec(
            select(GranularCertificateBundle.id).where(
                GranularCertificateBundle.id.in_(gc_bundle_ids),  # type: ignore[union-attr]
                GranularCertificateBundle.certificate_bundle_status
                == CertificateStatus.CANCELLED,
            )
        ).all()

        gc_bundle_ids_not_in_db = set(gc_bundle_ids) - set(gc_bundles_ids_in_db)
        if len(gc_bundle_ids_not_in_db) > 0:
            raise ValueError(
                f"One or more specified GC bundle IDs do not exist or have not been cancelled: {gc_bundle_ids_not_in_db}"
            )

    # Iterate through allocation records in the submission and verify that each
    # validator ID has a corresponding storage record
    updated_sdr_ids = []
    updated_scr_ids = []
    for _idx, allocation_record in allocated_storage_records_df.iterrows():
        sdr_mask = (
            validator_storage_records_df["id"] == allocation_record["sdr_allocation_id"]
        )
        scr_mask = (
            validator_storage_records_df["id"] == allocation_record["scr_allocation_id"]
        )
        if sdr_mask.sum() > 1 or scr_mask.sum() > 1:
            raise ValueError(
                f"Multiple storage records found for the specified allocation IDs: \
                                {allocation_record['sdr_allocation_id']} and {allocation_record['scr_allocation_id']}"
            )

        sdr = validator_storage_records_df.loc[allocation_record["sdr_allocation_id"]]
        scr = validator_storage_records_df.loc[allocation_record["scr_allocation_id"]]

        validate_allocated_records(allocation_record, sdr, scr)

        # Replace the allocation validator IDs with the registry database IDs
        updated_sdr_ids.append(sdr["id"])
        updated_scr_ids.append(scr["id"])

    allocated_storage_records_df["sdr_allocation_id"] = updated_sdr_ids
    allocated_storage_records_df["scr_allocation_id"] = updated_scr_ids

    # Convert NaN values to None for integer fields before creating records
    if "gc_allocation_id" in allocated_storage_records_df.columns:
        allocated_storage_records_df["gc_allocation_id"] = allocated_storage_records_df[
            "gc_allocation_id"
        ].where(pd.notna(allocated_storage_records_df["gc_allocation_id"]), None)

    if "sdgc_allocation_id" in allocated_storage_records_df.columns:
        allocated_storage_records_df["sdgc_allocation_id"] = (
            allocated_storage_records_df[
                "sdgc_allocation_id"
            ].where(pd.notna(allocated_storage_records_df["sdgc_allocation_id"]), None)
        )

    # Create the allocated storage records
    allocated_storage_records = AllocatedStorageRecord.create(
        allocated_storage_records_df.to_dict(orient="records"),
        write_session,
        read_session,
        esdb_client,
    )

    allocated_storage_records_cast = cast(
        list[AllocatedStorageRecord], allocated_storage_records
    )

    return allocated_storage_records_cast


def get_max_certificate_id_by_device_id(
    db_session: Session, device_id: int
) -> int | None:
    """Gets the maximum certificate ID from any bundle for a given device, excluding any withdrawn certificates.

    Args:
        db_session (Session): The database session
        device_id (int): The device ID

    Returns:
        int | None: The maximum certificate ID
    """

    stmt: SelectOfScalar = select(
        func.max(GranularCertificateBundle.certificate_bundle_id_range_end)
    ).where(
        GranularCertificateBundle.device_id == device_id,
        GranularCertificateBundle.certificate_bundle_status
        != CertificateStatus.WITHDRAWN,
    )

    max_certificate_id = db_session.exec(stmt).first()

    if not max_certificate_id:
        return None
    else:
        return int(max_certificate_id)


def issue_sdgcs_against_allocated_records(
    allocated_storage_records: list[AllocatedStorageRecord],
    device: Device,
    account_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> list[SQLModel]:
    """Issue SDGCs against the specified allocated storage records."""

    # Check that all the allocated storage records have associated GC Bundles
    if not all(record.gc_allocation_id for record in allocated_storage_records):
        raise ValueError(
            "All allocated storage records must have an associated GC Bundle ID."
        )

    # Retrieve the GC Bundles that have been cancelled and are associated with the allocated storage records
    cancelled_gc_bundles = read_session.exec(
        select(GranularCertificateBundle).where(
            GranularCertificateBundle.id.in_(  # type: ignore[union-attr]
                [record.gc_allocation_id for record in allocated_storage_records]
            ),
            GranularCertificateBundle.certificate_bundle_status
            == CertificateStatus.CANCELLED,
        )
    ).all()

    # Retrieve the associated SCRs/SDRs for the allocated storage records
    scr_ids = [record.scr_allocation_id for record in allocated_storage_records]
    sdr_ids = [record.sdr_allocation_id for record in allocated_storage_records]
    charge_records = read_session.exec(
        select(StorageRecord).where(StorageRecord.id.in_(scr_ids + sdr_ids))  # type: ignore[union-attr]
    ).all()

    # Validate that the GC Bundles have sufficient quantities and datetimes to cover the allocated storage records
    validate_allocated_records_against_gc_bundles(
        allocated_storage_records, charge_records, cancelled_gc_bundles
    )

    # Update a copy of the retrieved GC Bundles with the storage-specific attributes to pass through to the SDGC
    sdgcs_to_issue = []
    for allocated_storage_record in allocated_storage_records:
        cancelled_gc_bundle = next(
            (
                bundle
                for bundle in cancelled_gc_bundles
                if bundle.id == allocated_storage_record.gc_allocation_id
            ),
            None,
        )
        if cancelled_gc_bundle:
            cancelled_gc_bundle_attrs = cancelled_gc_bundle.model_dump()
            for attr in [
                "id",
                "status",
                "certificate_bundle_id_range_start",
                "certificate_bundle_id_range_end",
            ]:
                cancelled_gc_bundle_attrs.pop(attr)
            cancelled_gc_bundle_attrs["is_storage"] = True
            cancelled_gc_bundle_attrs["allocated_storage_record_id"] = (
                allocated_storage_record.id
            )
            cancelled_gc_bundle_attrs["storage_efficiency_factor"] = (
                allocated_storage_record.storage_efficiency_factor
            )
            sdgcs_to_issue.append(cancelled_gc_bundle_attrs)

    # Get SDRs for the specified allocation records
    sdr_ids = [record.sdr_allocation_id for record in allocated_storage_records]
    sdr_records = read_session.exec(
        select(StorageRecord).where(StorageRecord.id.in_(sdr_ids))  # type: ignore[union-attr]
    ).all()
    sdr_records_df = pd.DataFrame(sdr_records)

    # Get the max certificate bundle ID for the specified device
    if not device.id:
        raise ValueError("Device ID not found.")

    max_certificate_bundle_id = get_max_certificate_id_by_device_id(
        read_session, device.id
    )

    if max_certificate_bundle_id is None:
        raise ValueError(f"No certificate bundles found for device ID {device.id}.")

    mapped_sdgcs = map_allocation_to_certificates(
        sdgcs_to_issue=sdgcs_to_issue,
        sdr_records_df=sdr_records_df,
        account_id=account_id,
        device=device,
        certificate_bundle_id_range_start=max_certificate_bundle_id + 1,
    )

    # Create the SDGCs
    issued_sdgcs = GranularCertificateBundle.create(
        mapped_sdgcs, write_session, read_session, esdb_client
    )

    if not issued_sdgcs:
        raise ValueError("No SDGCs were created. Please check the input data.")

    issued_sdgcs_cast = cast(list[GranularCertificateBundle], issued_sdgcs)

    # Update the allocation records with the SDGC IDs
    for allocated_storage_record in allocated_storage_records:
        sdgc_id = next(
            (
                sdgc.id
                for sdgc in issued_sdgcs_cast
                if sdgc.allocated_storage_record_id == allocated_storage_record.id
            ),
            None,
        )
        if sdgc_id:
            allocated_storage_record.sdgc_allocation_id = sdgc_id
        else:
            raise ValueError(
                f"No SDGC found for allocated storage record ID {allocated_storage_record.id}"
            )

    # Update the allocation records in the database
    write_session.add_all(allocated_storage_records)
    write_session.commit()

    return issued_sdgcs


def map_allocation_to_certificates(
    sdgcs_to_issue: list[dict[str, Any]],
    sdr_records_df: pd.DataFrame,
    account_id: int,
    device: Device,
    certificate_bundle_id_range_start: int = 0,
) -> list[dict[Hashable, Any]]:
    mapped_data: list = []
    for sdgc in sdgcs_to_issue:
        sdr = sdr_records_df.loc[
            sdr_records_df["id"] == sdgc["allocated_storage_record_id"]
        ]

        # Get existing "certificate_bundle_id_range_end" from the last item in mapped_data
        if mapped_data:
            certificate_bundle_id_range_start = (
                mapped_data[-1]["certificate_bundle_id_range_end"] + 1
            )

        # E.g., if bundle_wh = 1000, certificate_bundle_id_range_start = 0, certificate_bundle_id_range_end = 999
        certificate_bundle_id_range_end = (
            certificate_bundle_id_range_start + sdr["flow_energy"] - 1
        )

        transformed = {
            "account_id": account_id,
            "allocated_storage_record_id": sdgc["allocated_storage_record_id"],
            "certificate_bundle_status": CertificateStatus.ACTIVE,
            "certificate_bundle_id_range_start": certificate_bundle_id_range_start,
            "certificate_bundle_id_range_end": certificate_bundle_id_range_end,
            "bundle_quantity": sdr["flow_energy"],
            "energy_carrier": EnergyCarrierType.electricity,
            "energy_source": EnergySourceType.battery_storage,
            "face_value": 1,
            "issuance_post_energy_carrier_conversion": True,
            "device_id": device.id,
            "production_starting_interval": sdr["flow_start_datetime"],
            "production_ending_interval": sdr["flow_end_datetime"],
            "issuance_datestamp": datetime.datetime.now(
                tz=datetime.timezone.utc
            ).date(),
            "expiry_datestamp": (
                datetime.datetime.now(tz=datetime.timezone.utc)
                + datetime.timedelta(days=365 * settings.CERTIFICATE_EXPIRY_YEARS)
            ).date(),
            "metadata_id": sdgc["issuance_metadata_id"],
            "is_storage": True,
            "hash": "Some hash",
        }

        transformed["issuance_id"] = (
            f"{device.id}-{transformed['production_starting_interval']}"
        )

        transformed["hash"] = create_bundle_hash(transformed, nonce="")

        mapped_data.append(transformed)

    return mapped_data
