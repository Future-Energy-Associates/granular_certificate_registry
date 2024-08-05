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
router = APIRouter(tags=["Organisations"])


def process_uuid(uuid_: uuid.UUID):
    if environment == "STAGE":
        uuid_ = str(uuid_).replace("-", "")

    return uuid_


# organisation
@router.post("/organisation", response_model=entities.OrganisationRead)
def create_organisation(
    organisation: entities.OrganisationBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_organisation = entities.Organisation.create(organisation, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=entities.OrganisationRead
    )


@router.get("/organisation/{organisation_id}", response_model=entities.OrganisationRead)
def read_organisation(
    organisation_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_organisation = entities.Organisation.by_id(
        process_uuid(organisation_id), session
    )

    return utils.format_json_response(
        db_organisation, headers, response_model=entities.OrganisationRead
    )


@router.patch(
    "/organisation/{organisation_id}", response_model=entities.OrganisationRead
)
def update_organisation(
    organisation: entities.OrganisationUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_organisation = entities.Organisation.by_id(
        process_uuid(organisation.organisation_id), session
    )
    db_organisation.update(organisation, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=entities.OrganisationRead
    )


@router.delete(
    "/organisation/{organisation_id}", response_model=entities.OrganisationRead
)
def delete_organisation(
    organisation_id: uuid.UUID,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["production"].yield_session),
):
    db_organisation = entities.Organisation.by_id(organisation_id, session)
    db_organisation.delete(session)

    return utils.format_json_response(
        db_organisation, headers, response_model=entities.OrganisationRead
    )
