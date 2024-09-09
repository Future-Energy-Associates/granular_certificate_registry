from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.crud import authentication
from gc_registry.database import db
from gc_registry.schemas import measurement

# Router initialisation
router = APIRouter(tags=["Miscellaneous"])


# # MeasurementReport
@router.post("/measurementreport", response_model=measurement.MeasurementReportRead)
def create_measurementreport(
    measurement_report_base: measurement.MeasurementReportBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = measurement.MeasurementReport.create(
        measurement_report_base, session
    )

    return utils.format_json_response(
        db_measurementreport, headers, response_model=measurement.MeasurementReportRead
    )


@router.get(
    "/measurementreport/{measurement_report_id}",
    response_model=measurement.MeasurementReportRead,
)
def read_measurementreport(
    measurement_report_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = measurement.MeasurementReport.by_id(
        measurement_report_id, session
    )

    return utils.format_json_response(
        db_measurementreport, headers, response_model=measurement.MeasurementReportRead
    )


@router.patch(
    "/measurementreport/{measurement_report_id}",
    response_model=measurement.MeasurementReportRead,
)
def update_measurementreport(
    measurement_report_update: measurement.MeasurementReportUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = measurement.MeasurementReport.by_id(
        measurement_report_update.measurement_report_id, session
    )
    db_measurementreport.update(measurement_report_update, session)

    return utils.format_json_response(
        db_measurementreport, headers, response_model=measurement.MeasurementReportRead
    )


@router.delete(
    "/measurementreport/{measurement_report_id}",
    response_model=measurement.MeasurementReportRead,
)
def delete_measurementreport(
    measurement_report_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_measurementreport = measurement.MeasurementReport.by_id(
        measurement_report_id, session
    )
    db_measurementreport.delete(session)

    return utils.format_json_response(
        db_measurementreport, headers, response_model=measurement.MeasurementReportRead
    )
