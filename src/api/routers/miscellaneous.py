# Imports
import os
import uuid

from energytag.api import utils
from energytag.api.routers import authentication
from energytag.datamodel import db
from energytag.datamodel.schemas import entities
from fastapi import APIRouter, Depends
from sqlmodel import Session

environment = os.getenv("ENVIRONMENT")


# Router initialisation
router = APIRouter(tags=["Miscellaneous"])


def process_uuid(uuid_: uuid.UUID):
    if environment == "STAGE":
        uuid_ = str(uuid_).replace("-", "")

    return uuid_

# Image
@router.post("/image", response_model=entities.ImageRead)
def create_image(
    image: entities.ImageBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_image = entities.Image.create(image, session)

    return utils.format_json_response(
        db_image, headers, response_model=entities.ImageRead
    )


@router.get("/image/{image_id}", response_model=entities.ImageRead)
def read_image(
    image_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_image = entities.Image.by_id(process_uuid(image_id), session)

    return utils.format_json_response(
        db_image, headers, response_model=entities.ImageRead
    )


@router.patch("/image/{image_id}", response_model=entities.ImageRead)
def update_image(
    image: entities.ImageUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_image = entities.Image.by_id(process_uuid(image.image_id), session)
    db_image.update(image, session)

    return utils.format_json_response(
        db_image, headers, response_model=entities.ImageRead
    )


@router.delete("/image/{image_id}", response_model=entities.ImageRead)
def delete_image(
    image_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_image = entities.Image.by_id(image_id, session)
    db_image.delete(session)

    return utils.format_json_response(
        db_image, headers, response_model=entities.ImageRead
    )


# # Location
@router.post("/location", response_model=entities.LocationRead)
def create_location(
    location: entities.LocationBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_location = entities.Location.create(location, session)

    return utils.format_json_response(
        db_location, headers, response_model=entities.LocationRead
    )


@router.get("/location/{location_id}", response_model=entities.LocationRead)
def read_location(
    location_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    print(location_id)
    print(process_uuid(location_id))
    db_location = entities.Location.by_id(process_uuid(location_id), session)

    return utils.format_json_response(
        db_location, headers, response_model=entities.LocationRead
    )


@router.patch("/location/{location_id}", response_model=entities.LocationRead)
def update_location(
    location: entities.LocationUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_location = entities.Location.by_id(process_uuid(location.location_id), session)
    db_location.update(location, session)

    return utils.format_json_response(
        db_location, headers, response_model=entities.LocationRead
    )


@router.delete("/location/{location_id}", response_model=entities.LocationRead)
def delete_location(
    location_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_location = entities.Location.by_id(location_id, session)
    db_location.delete(session)

    return utils.format_json_response(
        db_location, headers, response_model=entities.LocationRead
    )


# # MeasurementReport
@router.post("/measurementreport", response_model=entities.MeasurementReportRead)
def create_measurementreport(
    measurementreport: entities.MeasurementReportBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
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
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_measurementreport = entities.MeasurementReport.by_id(
        process_uuid(measurement_report_id), session
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
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_measurementreport = entities.MeasurementReport.by_id(
        process_uuid(measurementreport.measurement_report_id), session
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
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_measurementreport = entities.MeasurementReport.by_id(
        measurement_report_id, session
    )
    db_measurementreport.delete(session)

    return utils.format_json_response(
        db_measurementreport, headers, response_model=entities.MeasurementReportRead
    )


# Meter
@router.post("/meter", response_model=entities.MeterRead)
def create_meter(
    meter: entities.MeterBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_meter = entities.Meter.create(meter, session)

    return utils.format_json_response(
        db_meter, headers, response_model=entities.MeterRead
    )


@router.get("/meter/{meter_id}", response_model=entities.MeterRead)
def read_meter(
    meter_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_meter = entities.Meter.by_id(process_uuid(meter_id), session)

    return utils.format_json_response(
        db_meter, headers, response_model=entities.MeterRead
    )


@router.patch("/meter/{meter_id}", response_model=entities.MeterRead)
def update_meter(
    meter: entities.MeterUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_meter = entities.Meter.by_id(process_uuid(meter.meter_id), session)
    db_meter.update(meter, session)

    return utils.format_json_response(
        db_meter, headers, response_model=entities.MeterRead
    )


@router.delete("/meter/{meter_id}", response_model=entities.MeterRead)
def delete_meter(
    meter_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_meter = entities.Meter.by_id(meter_id, session)
    db_meter.delete(session)

    return utils.format_json_response(
        db_meter, headers, response_model=entities.MeterRead
    )


# SubsidySupport
@router.post("/subsidysupport", response_model=entities.SubsidySupportRead)
def create_subsidysupport(
    subsidysupport: entities.SubsidySupportBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_subsidysupport = entities.SubsidySupport.create(subsidysupport, session)

    return utils.format_json_response(
        db_subsidysupport, headers, response_model=entities.SubsidySupportRead
    )


@router.get(
    "/subsidysupport/{subsidy_support_id}", response_model=entities.SubsidySupportRead
)
def read_subsidysupport(
    subsidy_support_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_subsidysupport = entities.SubsidySupport.by_id(
        process_uuid(subsidy_support_id), session
    )

    return utils.format_json_response(
        db_subsidysupport, headers, response_model=entities.SubsidySupportRead
    )


@router.patch(
    "/subsidysupport/{subsidy_support_id}", response_model=entities.SubsidySupportRead
)
def update_subsidysupport(
    subsidysupport: entities.SubsidySupportUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_subsidysupport = entities.SubsidySupport.by_id(
        process_uuid(subsidysupport.subsidy_support_id), session
    )
    db_subsidysupport.update(subsidysupport, session)

    return utils.format_json_response(
        db_subsidysupport, headers, response_model=entities.SubsidySupportRead
    )


@router.delete(
    "/subsidysupport/{subsidy_support_id}", response_model=entities.SubsidySupportRead
)
def delete_subsidysupport(
    subsidy_support_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_subsidysupport = entities.SubsidySupport.by_id(subsidy_support_id, session)
    db_subsidysupport.delete(session)

    return utils.format_json_response(
        db_subsidysupport, headers, response_model=entities.SubsidySupportRead
    )
