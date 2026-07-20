# Imports
import io
from pathlib import Path

import pandas as pd
from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.services import (
    get_latest_issuance_metadata,
    issue_certificates_by_device_in_date_range,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.device.meter_data.manual_submission import ManualSubmissionMeterClient
from gc_registry.device.models import Device
from gc_registry.logging_config import log_context, logger
from gc_registry.measurement.models import MeasurementReport
from gc_registry.measurement.schemas import (
    MeasurementReportBase,
    MeasurementReportRead,
    MeasurementReportUpdate,
    MeasurementSubmissionResponse,
)
from gc_registry.measurement.validation import validate_readings
from gc_registry.user.models import User
from gc_registry.user.validation import validate_user_access, validate_user_role

# Router initialisation
router = APIRouter(tags=["Measurements"])


### Device Meter Readings ###


@router.get("/meter_readings_template", response_class=FileResponse)
def get_meter_readings_template(current_user: User = Depends(get_current_user)):
    """Return the CSV template for meter readings submission."""
    template_path = (
        Path(__file__).parent.parent
        / "static"
        / "templates"
        / "meter_readings_template.csv"
    )

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")

    return FileResponse(
        path=template_path,
        filename="meter_readings_template.csv",
        media_type="text/csv",
    )


@router.post("/submit_readings", response_model=MeasurementSubmissionResponse)
async def submit_readings(
    file: UploadFile = File(...),
    device_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Submit meter readings as a CSV file for a single device,
    creating a MeasurementReport for each production interval against which GC
    Bundles can be issued. Returns a summary of the readings submitted.

    Until an issuance metadata workflow is implemented, the submission will use a
    default set of issuance metadata. In the front end, this will be implemented as
    a dialogue box that presents the user with the default metadata values, and allow
    them to edit them if desired at the point of issuance.

    Args:
        file (UploadFile): The CSV file containing meter readings
        device_id (int): The ID of the device the readings are for

    Returns:
        models.MeasurementSubmissionResponse: A summary of the readings submitted.
    """
    with log_context(
        operation="submit_readings",
        device_id=device_id,
        user_id=current_user.id,
        filename=file.filename,
    ):
        validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

        # Read the uploaded file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode("utf-8"))

        # Convert to DataFrame
        measurement_df = pd.read_csv(csv_file)
        measurement_df["device_id"] = device_id
        logger.info(
            "Meter readings CSV parsed", extra={"row_count": len(measurement_df)}
        )

        passed, measurement_df, message = validate_readings(measurement_df)
        if not passed:
            logger.warning(
                "Meter readings validation failed", extra={"reason": message}
            )
            raise HTTPException(
                status_code=400,
                detail=message,
            )

        # Check that the device ID is associated with an account that the user has access to
        device = Device.by_id(device_id, read_session)

        logger.info(
            "Device lookup completed", extra={"device_found": device is not None}
        )

        if not device:
            raise HTTPException(
                status_code=404, detail=f"Device with ID {device_id} not found."
            )

        validate_user_access(current_user, device.account_id, read_session)

        readings = MeasurementReport.create(
            measurement_df.to_dict(orient="records"),
            write_session,
            read_session,
            esdb_client,
        )

        if not readings:
            raise HTTPException(
                status_code=500, detail="Could not create measurement reports."
            )

        logger.info(
            "Measurement reports created", extra={"report_count": len(readings)}
        )

        # issue GCs against these readings
        meter_data_client = ManualSubmissionMeterClient()

        # if no issuance metadata is in the database, create a default entry and link
        # issuance to that. This is where the values passed by the user will be attached
        # following an upstream process on the front end.

        # TODO: Implement issuance metadata creation process linked to device
        issuance_metadata = get_latest_issuance_metadata(read_session)

        if not issuance_metadata:
            raise HTTPException(
                status_code=404, detail="Could not find issuance metadata."
            )

        try:
            measurement_response = MeasurementSubmissionResponse(
                message="Readings submitted successfully.",
                total_device_usage=measurement_df["interval_usage"].astype(int).sum(),
                first_reading_datetime=pd.to_datetime(
                    measurement_df["interval_start_datetime"].min(), utc=True
                ),
                last_reading_datetime=pd.to_datetime(
                    measurement_df["interval_start_datetime"].max(), utc=True
                ),
            )
            issue_certificates_by_device_in_date_range(
                device=device,
                from_datetime=pd.to_datetime(
                    measurement_df["interval_start_datetime"].min(), utc=True
                ),
                to_datetime=pd.to_datetime(
                    measurement_df["interval_end_datetime"].max(), utc=True
                ),
                write_session=write_session,
                read_session=read_session,
                esdb_client=esdb_client,
                issuance_metadata_id=issuance_metadata.id,
                meter_data_client=meter_data_client,
            )
            logger.info(
                "Meter readings submitted and GCs issued",
                extra={"total_usage": measurement_response.total_device_usage},
            )
        except Exception as e:
            logger.error("Error issuing GCs", extra={"error": str(e)})
            raise HTTPException(status_code=400, detail=f"Error issuing GCs: {str(e)}")

        return measurement_response


@router.post("/create", response_model=MeasurementReportRead)
def create_measurement(
    measurement_base: MeasurementReportBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)

    device = Device.by_id(measurement_base.device_id, read_session)
    validate_user_access(current_user, device.account_id, read_session)

    measurement = MeasurementReport.create(
        measurement_base, write_session, read_session, esdb_client
    )

    return measurement


@router.get("/{measurement_id}", response_model=MeasurementReportRead)
def read_measurement(
    measurement_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)

    measurement = MeasurementReport.by_id(measurement_id, read_session)

    return measurement


@router.patch("/update/{measurement_id}", response_model=MeasurementReportRead)
def update_measurement(
    measurement_id: int,
    measurement_update: MeasurementReportUpdate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    # Measurement updates are only allowed for Admin users as GCs may have been issued against them
    validate_user_role(current_user, required_role=UserRoles.ADMIN)

    measurement = MeasurementReport.by_id(measurement_id, read_session)

    return measurement.update(
        measurement_update, write_session, read_session, esdb_client
    )


@router.delete("/delete/{id}", response_model=MeasurementReportRead)
def delete_measurement(
    measurement_id: int,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    # Measurement deletions are only allowed for Admin users as GCs may have been issued against them
    validate_user_role(current_user, required_role=UserRoles.ADMIN)

    db_measurement = MeasurementReport.by_id(measurement_id, write_session)

    return db_measurement.delete(write_session, read_session, esdb_client)
