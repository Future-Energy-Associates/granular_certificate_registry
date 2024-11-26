# Imports
from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from gc_registry.core.database import db, events
from gc_registry.measurement import models
from gc_registry.measurement.services import parse_measurement_json

# Router initialisation
router = APIRouter(tags=["Measurements"])

### Device Meter Readings ###


@router.post("/submit_readings", response_model=models.MeasurementSubmissionResponse)
def submit_readings(
    measurement_json: str,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Submit meter readings as a JSON-serialised CSV file for one or more devices,
    creating a MeasurementReport for each production interval against which GC
    Bundles can be issued. Returns a summary of the readings submitted.

    Args:
        measurement_json (str): A JSON-serialised CSV file containing the meter readings.

    Returns:
        models.MeasurementSubmissionResponse: A summary of the readings submitted.
    """
    measurement_df = parse_measurement_json(measurement_json, to_df=True)

    readings = models.MeasurementReport.create(
        measurement_df.to_dict(orient="records"),
        write_session,
        read_session,
        esdb_client,
    )

    if not readings:
        raise HTTPException(
            status_code=500, detail="Could not create measurement reports."
        )

    measurement_response = models.MeasurementSubmissionResponse(
        message="Readings submitted successfully.",
        total_usage_per_device=measurement_df.groupby("device_id")["interval_usage"]
        .sum()
        .to_dict(),
        first_reading_datetime=measurement_df["interval_start_datetime"].min(),
        last_reading_datetime=measurement_df["interval_end_datetime"].max(),
    )

    return measurement_response


@router.post("/create", response_model=models.MeasurementReportRead)
def create_measurement(
    measurement_base: models.MeasurementReportBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    measurement = models.MeasurementReport.create(
        measurement_base, write_session, read_session, esdb_client
    )

    return measurement


@router.get("/{measurement_id}", response_model=models.MeasurementReportRead)
def read_measurement(
    measurement_id: int,
    read_session: Session = Depends(db.get_read_session),
):
    measurement = models.MeasurementReport.by_id(measurement_id, read_session)

    return measurement


@router.patch("/update/{measurement_id}", response_model=models.MeasurementReportRead)
def update_measurement(
    measurement_id: int,
    measurement_update: models.MeasurementReportUpdate,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    measurement = models.MeasurementReport.by_id(measurement_id, read_session)

    return measurement.update(
        measurement_update, write_session, read_session, esdb_client
    )


@router.delete("/delete/{id}", response_model=models.MeasurementReportRead)
def delete_measurement(
    measurement_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    db_measurement = models.MeasurementReport.by_id(measurement_id, write_session)
    return db_measurement.delete(write_session, read_session, esdb_client)
