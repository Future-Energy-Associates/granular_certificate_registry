from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.authentication import services
from gc_registry.core.database import cqrs, db
from gc_registry.organisation import models

# Router initialisation
router = APIRouter(tags=["Organisations"])


# organisation
@router.post("/organisation", response_model=models.OrganisationRead)
def create_organisation(
    organisation_base: models.OrganisationBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
):
    db_organisation = models.Organisation.create(organisation_base, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=models.OrganisationRead
    )


@router.get("/organisation/{id}", response_model=models.OrganisationRead)
def read_organisation(
    organisation_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    db_organisation = models.Organisation.by_id(organisation_id, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=models.OrganisationRead
    )


@router.patch("/organisation/{id}", response_model=models.OrganisationRead)
def update_organisation(
    organisation: models.OrganisationRead,
    organisation_update: models.OrganisationUpdate,
    headers: dict = Depends(services.validate_user_and_get_headers),
    write_session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
    read_session: Session = Depends(db.db_name_to_client["db_read"].yield_session),
):
    organisation_updated = cqrs.update_database_entity(
        organisation, organisation_update, write_session, read_session
    )

    return utils.format_json_response(
        organisation_updated, headers, response_model=models.OrganisationRead
    )


@router.delete("/organisation/{id}", response_model=models.OrganisationRead)
def delete_organisation(
    organisation_id: int,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["db_write"].yield_session),
):
    db_organisation = models.Organisation.by_id(organisation_id, session)
    db_organisation.delete(session)

    return utils.format_json_response(
        db_organisation, headers, response_model=models.OrganisationRead
    )
