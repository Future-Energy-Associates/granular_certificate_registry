from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.authentication import services
from gc_registry.core.database import db
from gc_registry.organisation import models

# Router initialisation
router = APIRouter(tags=["Organisations"])


# organisation
@router.post("/organisation", response_model=models.OrganisationRead)
def create_organisation(
    organisation_base: models.OrganisationBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_organisation = models.Organisation.create(organisation_base, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=models.OrganisationRead
    )


@router.get("/organisation/{id}", response_model=models.OrganisationRead)
def read_organisation(
    organisation_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_organisation = models.Organisation.by_id(organisation_id, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=models.OrganisationRead
    )


@router.patch("/organisation/{id}", response_model=models.OrganisationRead)
def update_organisation(
    organisation_update: models.OrganisationUpdate,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_organisation = models.Organisation.by_id(organisation_update.id, session)
    db_organisation.update(organisation_update, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=models.OrganisationRead
    )


@router.delete("/organisation/{id}", response_model=models.OrganisationRead)
def delete_organisation(
    organisation_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["write"].yield_session),
):
    db_organisation = models.Organisation.by_id(organisation_id, session)
    db_organisation.delete(session)

    return utils.format_json_response(
        db_organisation, headers, response_model=models.OrganisationRead
    )
