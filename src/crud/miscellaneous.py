# Imports
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src import utils
from src.crud import authentication
from src.database import db
from src.schemas import entities

# Router initialisation
router = APIRouter(tags=["Miscellaneous"])


# # MeasurementReport
@router.post("/measurementreport", response_model=entities.MeasurementReportRead)
def create_measurementreport(
    measurementreport: entities.MeasurementReportBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = entities.MeasurementReport.create(measurementreport, session)

    return utils.format_json_response(
        db_measurementreport, headers, response_model=entities.MeasurementReportRead
    )


@router.get(
    "/measurementreport/{measurement_report_id}",
    response_model=entities.MeasurementReportRead,
)
def read_measurementreport(
    measurement_report_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = entities.MeasurementReport.by_id(
        utils.process_uuid(measurement_report_id), session
    )

    return utils.format_json_response(
        db_measurementreport, headers, response_model=entities.MeasurementReportRead
    )


@router.patch(
    "/measurementreport/{measurement_report_id}",
    response_model=entities.MeasurementReportRead,
)
def update_measurementreport(
    measurementreport: entities.MeasurementReportUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = entities.MeasurementReport.by_id(
        utils.process_uuid(measurementreport.measurement_report_id), session
    )
    db_measurementreport.update(measurementreport, session)

    return utils.format_json_response(
        db_measurementreport, headers, response_model=entities.MeasurementReportRead
    )


@router.delete(
    "/measurementreport/{measurement_report_id}",
    response_model=entities.MeasurementReportRead,
)
def delete_measurementreport(
    measurement_report_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = entities.MeasurementReport.by_id(
        measurement_report_id, session
    )
    db_measurementreport.delete(session)

    return utils.format_json_response(
        db_measurementreport, headers, response_model=entities.MeasurementReportRead
    )
