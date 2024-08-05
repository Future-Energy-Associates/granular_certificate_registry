import os
import uuid

from api import utils
from api.routers import authentication
from datamodel import db, schemas
from fastapi import APIRouter, Depends
from sqlmodel import Session

# Router initialisation

router = APIRouter(tags=["Production"])
environment = os.getenv("ENVIRONMENT")


def process_uuid(uuid_: uuid.UUID):
    if environment == "STAGE":
        uuid_ = str(uuid_).replace("-", "")

    return uuid_


@router.post("/register-device/", response_model=schemas.api.RegisteringDeviceWrite)
def register_device(
    registering_device: schemas.api.RegisteringDeviceWrite,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    device_id = uuid.uuid4()

    _ = schemas.entities.Location.create(registering_device.location, session)
    location_id = _.location_id

    for meter in registering_device.meters:
        _ = schemas.entities.Meter.create(meter, session)

    _ = schemas.entities.Account.create(registering_device.account, session)
    account_id = _.account_id

    if registering_device.subsidy_support is not None:
        for subsidy_support in registering_device.subsidy_support:
            _ = schemas.entities.SubsidySupport.create(subsidy_support, session)

    if registering_device.images is not None:
        for image in registering_device.images:
            _ = schemas.entities.Meter.create(image, session)

    # for auxiliary_unit in registering_device.auxiliary_units:
    #     _ = schemas.entities.Meter.create(auxiliary_unit, session)

    # Constructing the device table object
    device_ = {
        k: v
        for k, v in registering_device.dict().items()
        if k
        in [
            "device_name",
            "grid",
            "energy_source",
            "technology_type",
            "operational_date",
            "capacity",
            "peak_demand",
        ]
    }

    device_.update(
        {"device_id": device_id, "location_id": location_id, "account_id": account_id}
    )

    _ = schemas.entities.Device.create(device_, session)

    # Loading device view
    # registered_device = session.get(schemas.entities.Device, device_id)

    return utils.format_json_response(
        registering_device,
        headers=headers,
        response_model=schemas.api.RegisteringDeviceWrite,
    )
