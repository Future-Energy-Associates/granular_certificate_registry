import os

from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.api import utils
from gc_registry.api.routers import authentication
from gc_registry.datamodel import db
from gc_registry.datamodel.schemas import api, entities

# Router initialisation

router = APIRouter(tags=["Production"])
environment = os.getenv("ENVIRONMENT")


@router.post("/register-device/", response_model=api.RegisteringDeviceWrite)
def register_device(
    registering_device: api.RegisteringDeviceWrite,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    # TODO: Work out if we need a location and meter table
    # _ = entities.Location.create(registering_device.location, session)
    # location_id = _.location_id

    # for meter in registering_device.meters:
    #     _ = entities.Meter.create(meter, session)

    account = entities.Account.create(registering_device.account, session)

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

    device_.update({"account_id": account.id})

    _ = entities.Device.create(device_, session)

    # Loading device view
    # registered_device = session.get(entities.Device, device_id)

    return utils.format_json_response(
        registering_device,
        headers=headers,
        response_model=api.RegisteringDeviceWrite,
    )
