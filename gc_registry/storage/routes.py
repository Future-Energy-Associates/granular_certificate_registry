import datetime
import io
from pathlib import Path
from typing import cast

import pandas as pd
from esdbclient import EventStoreDBClient
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.device.models import Device
from gc_registry.device.services import get_device_by_id
from gc_registry.logging_config import logger
from gc_registry.storage.models import (
    AllocatedStorageRecord,
    StorageRecord,
)
from gc_registry.storage.schemas import (
    AllocatedStorageRecordSubmissionResponse,
    StorageRecordSubmissionResponse,
)
from gc_registry.storage.services import (
    create_allocated_storage_records_from_submitted_data,
    create_charge_records_from_metering_data,
    issue_sdgcs_against_allocated_records,
)
from gc_registry.storage.utils import (
    get_allocated_storage_records_by_device_id,
    get_allocated_storage_records_by_id,
    get_device_ids_in_allocated_storage_records,
    get_storage_records_by_id,
)
from gc_registry.storage.validation import (
    validate_access_to_devices,
    validate_storage_records,
)
from gc_registry.user.models import User
from gc_registry.user.validation import (
    validate_user_access,
    validate_user_role,
    validate_user_role_for_storage_validator,
)

# Router initialisation
router = APIRouter(tags=["Storage"])


@router.get("/storage_readings_template", response_class=FileResponse)
def get_storage_readings_template(current_user: User = Depends(get_current_user)):
    """Return the CSV template for storage readings submission."""
    template_path = (
        Path(__file__).parent.parent
        / "static"
        / "templates"
        / "storage_readings_template.csv"
    )

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")

    return FileResponse(
        path=template_path,
        filename="meter_readings_template.csv",
        media_type="text/csv",
    )


@router.get("/storage_allocation_template", response_class=FileResponse)
def get_storage_allocation_template(current_user: User = Depends(get_current_user)):
    """Return the CSV template for storage allocation submission."""
    template_path = (
        Path(__file__).parent.parent
        / "static"
        / "templates"
        / "storage_allocation_template.csv"
    )

    if not template_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template file not found."
        )

    return FileResponse(
        path=template_path,
        filename="storage_allocation_template.csv",
        media_type="text/csv",
    )


@router.post(
    "/storage_records",
    response_model=StorageRecordSubmissionResponse,
    status_code=201,
)
async def submit_storage_records(
    file: UploadFile = File(...),
    device_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> StorageRecordSubmissionResponse:
    """Submit a list of Storage Records to the registry."""

    # Can be performed by both Storage Device owners and Storage Validators
    if current_user.role != UserRoles.STORAGE_VALIDATOR:
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    try:
        # Read the uploaded file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode("utf-8"))

        # Convert to DataFrame
        df = pd.read_csv(csv_file)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading CSV file: {str(e)}",
        )

    df["device_id"] = device_id

    device = get_device_by_id(read_session, device_id)
    logger.info(f"Device: {device}")

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found.",
        )

    if not device.is_storage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with ID {device_id} is not a storage device.",
        )

    passed, message = validate_storage_records(df, read_session, device_id)
    if not passed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid measurement data: {message}",
        )

    validate_user_access(current_user, device.account_id, read_session)

    # Create the storage records
    storage_submission_response = create_charge_records_from_metering_data(
        df,
        write_session,
        read_session,
        esdb_client,
    )

    return StorageRecordSubmissionResponse.model_validate(storage_submission_response)


@router.get(
    "/storage_records",
    response_model=list[StorageRecord],
    status_code=200,
)
async def get_storage_records_by_id_route(
    storage_record_ids: list[int] = Query(
        ...,
        description="The IDs of the storage records to return.",
        example=[1, 2, 3],
    ),
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Return storage records for the specified IDs.

    Verifies that the user has access to the devices associated with
    the storage records prior to returning them.

    Args:
        storage_record_ids (list[int]): The IDs of the storage records to return.
        current_user (User): The current user.
        read_session (Session): The database session.

    Returns:
        list[StorageRecord]: The storage records for the specified IDs.
    """
    # Can be performed by both Storage Device owners and Storage Validators
    if current_user.role != UserRoles.STORAGE_VALIDATOR:
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    storage_records = get_storage_records_by_id(storage_record_ids, read_session)
    if not storage_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No storage records found for the specified IDs.",
        )

    # Check that the user has access to the devices associated with the storage records
    device_ids = {record.device_id for record in storage_records}

    validate_access_to_devices(device_ids, current_user, read_session)

    return storage_records


@router.post(
    "/allocated_storage_records",
    response_model=AllocatedStorageRecordSubmissionResponse,
    status_code=201,
)
async def create_storage_allocation(
    file: UploadFile = File(...),
    device_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> AllocatedStorageRecordSubmissionResponse:
    """Storage Validator Only: Submit a list of Allocated Storage Records to the registry.

    This endpoint depends on there being existing validated Storage Charge/Discharge Records
    that have been submitted for the specified device.
    """
    validate_user_role_for_storage_validator(current_user)

    try:
        # Read the uploaded file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode("utf-8"))

        # Convert to DataFrame and replace NaN values with None
        allocated_storage_records_df = pd.read_csv(csv_file, keep_default_na=False)
        allocated_storage_records_df["device_id"] = device_id

        # Check that the device ID is associated with an account that the user has access to
        device = Device.by_id(device_id, read_session)

        logger.info(f"Device: {device}")

        if not device:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {device_id} not found."
            )
        if not device.is_storage:
            raise HTTPException(
                status_code=400,
                detail=f"Device with ID {device_id} is not a storage device.",
            )

        validate_user_access(current_user, device.account_id, read_session)

        # Create the allocated storage records
        allocated_storage_records = (
            create_allocated_storage_records_from_submitted_data(
                allocated_storage_records_df,
                write_session,
                read_session,
                esdb_client,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if allocated_storage_records is None:
        raise HTTPException(
            status_code=400,
            detail="No valid allocated storage records were created from the submitted data.",
        )

    allocated_storage_records_cast = cast(
        list[AllocatedStorageRecord], allocated_storage_records
    )

    return AllocatedStorageRecordSubmissionResponse(
        total_records=len(allocated_storage_records_cast),
        record_ids=[record.id for record in allocated_storage_records_cast],
        message="Allocation records created successfully.",
    )


@router.post(
    "/issue_sdgcs",
    response_model=list[GranularCertificateBundle],
    status_code=200,
)
def issue_SDGCs(
    allocated_storage_record_ids: list[int],
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """A GC Bundle that has been issued following the verification of a cancelled GC Bundle and the proper allocation of a pair
    of Storage Charge and Discharge Records. The GC Bundle is issued to the Account of the Storage Device, and is identical to
    a GC Bundle issued to a production Device albeit with additional storage-specific attributes as described in the Standard.
    These bundles can be queried using the same GC Bundle query endpoint as regular GC Bundles, but with the additional option to filter
    by the storage_id and the discharging_start_datetime, which is inherited from the allocated SDR.
    """
    if current_user.role != UserRoles.STORAGE_VALIDATOR:
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    try:
        # Retrieve the allocated storage records
        allocated_storage_records = read_session.exec(
            select(AllocatedStorageRecord).where(
                AllocatedStorageRecord.id.in_(allocated_storage_record_ids)  # type: ignore
            )
        ).all()

        # Assert allocation records for a single device have been submitted
        device_ids = [record.device_id for record in allocated_storage_records]
        if len(device_ids) != 1:
            raise HTTPException(
                status_code=400,
                detail="Allocation records must be for a single device.",
            )
        device_id = device_ids[0]
        device = Device.by_id(device_id, read_session)

        # Assert the user has access to the specified device
        validate_user_access(current_user, device.account_id, read_session)

        issued_sdgcs = issue_sdgcs_against_allocated_records(
            allocated_storage_records=allocated_storage_records,
            device=device,
            account_id=device.account_id,
            write_session=write_session,
            read_session=read_session,
            esdb_client=esdb_client,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return issued_sdgcs


@router.get(
    "/allocated_storage_records_by_id",
    response_model=list[AllocatedStorageRecord],
    status_code=200,
)
def get_allocated_storage_records_by_id_route(
    allocated_storage_record_ids: list[int] = Query(
        ...,
        description="The IDs of the allocated storage records to return.",
        example=[1, 2, 3],
    ),
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Return allocated storage records for the specified IDs.

    Verifies that the user has access to the devices associated with
    the allocated storage records prior to returning them.

    Args:
        allocated_storage_record_ids (list[int]): The IDs of the allocated storage records to return.
        current_user (User): The current user.
        read_session (Session): The database session.

    Returns:
        list[AllocatedStorageRecord]: The allocated storage records for the specified IDs.
    """

    # Can be performed by both Storage Device owners and Storage Validators
    if current_user.role != UserRoles.STORAGE_VALIDATOR:
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    allocated_storage_records = get_allocated_storage_records_by_id(
        allocated_storage_record_ids, read_session
    )
    if not allocated_storage_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No allocated storage records found for the specified IDs.",
        )

    # Check that the user has access to the devices associated with the allocated storage records
    device_ids = {record.device_id for record in allocated_storage_records}

    validate_access_to_devices(device_ids, current_user, read_session)

    return allocated_storage_records


@router.get(
    "/allocated_storage_records/{device_id}",
    response_model=list[AllocatedStorageRecord],
    status_code=200,
)
def get_allocated_storage_records(
    device_id: int,
    current_user: User = Depends(get_current_user),
    created_after: datetime.date | None = None,
    created_before: datetime.date | None = None,
    read_session: Session = Depends(db.get_read_session),
):
    """Retrieve all allocated storage records."""

    if current_user.role != UserRoles.STORAGE_VALIDATOR:
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    # check that the device_id is valid
    device_ids = get_device_ids_in_allocated_storage_records(read_session)

    if not device_ids or device_id not in device_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID {device_id} not found in allocated storage records.",
        )

    validate_access_to_devices([device_id], current_user, read_session)

    if not created_after:
        created_after = (datetime.datetime.now() - datetime.timedelta(days=7)).date()
    if not created_before:
        created_before = (datetime.datetime.now() + datetime.timedelta(days=1)).date()

    # Validate the date range
    if created_after and created_before and created_after >= created_before:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="created_after must be before created_before.",
        )
    # check the difference between created_after and created_before is not too large
    date_difference = (created_before - created_after).days
    if date_difference > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 30 days.",
        )

    # Retrieve allocated storage records for the specified device
    allocated_storage_records = get_allocated_storage_records_by_device_id(
        device_id=device_id,
        read_session=read_session,
        created_after=created_after or datetime.date.min,
        created_before=created_before or datetime.date.max,
    )

    return allocated_storage_records
