# Imports
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.authentication import services
from gc_registry.core.database import db
from gc_registry.measurement import models

# Router initialisation
router = APIRouter(tags=["Measurements"])

### Device Meter Readings ###


@router.post("/measurement", response_model=models.MeasurementReportRead)
def create_measurement(
    measurement_base: models.MeasurementReportBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_measurement = models.MeasurementReport.create(measurement_base, session)

    return utils.format_json_response(
        db_measurement, headers, response_model=models.MeasurementReportRead
    )


@router.get("/measurement/{id}", response_model=models.MeasurementReportRead)
def read_measurement(
    measurement_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurement = models.MeasurementReport.by_id(measurement_id, session)

    return utils.format_json_response(
        db_measurement, headers, response_model=models.MeasurementReportRead
    )


@router.patch("/measurement/{id}", response_model=models.MeasurementReportRead)
def update_measurement(
    measurement_update: models.MeasurementReportUpdate,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_measurement = models.MeasurementReport.by_id(measurement_update.id, session)
    db_measurement.update(measurement_update, session)

    return utils.format_json_response(
        db_measurement, headers, response_model=models.MeasurementReportRead
    )


@router.delete("/measurement/{id}", response_model=models.MeasurementReportRead)
def delete_measurement(
    measurement_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_measurement = models.MeasurementReport.by_id(measurement_id, session)
    db_measurement.delete(session)

    return utils.format_json_response(
        db_measurement, headers, response_model=models.MeasurementReportRead
    )
