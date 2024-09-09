from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.crud import authentication
from gc_registry.database import db
from gc_registry.schemas import organisation

# Router initialisation
router = APIRouter(tags=["Organisations"])


# organisation
@router.post("/organisation", response_model=organisation.OrganisationRead)
def create_organisation(
    organisation_base: organisation.OrganisationBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_organisation = organisation.Organisation.create(organisation_base, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=organisation.OrganisationRead
    )


@router.get("/organisation/{id}", response_model=organisation.OrganisationRead)
def read_organisation(
    organisation_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_organisation = organisation.Organisation.by_id(organisation_id, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=organisation.OrganisationRead
    )


@router.patch("/organisation/{id}", response_model=organisation.OrganisationRead)
def update_organisation(
    organisation_update: organisation.OrganisationUpdate,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_organisation = organisation.Organisation.by_id(organisation_update.id, session)
    db_organisation.update(organisation_update, session)

    return utils.format_json_response(
        db_organisation, headers, response_model=organisation.OrganisationRead
    )


@router.delete("/organisation/{id}", response_model=organisation.OrganisationRead)
def delete_organisation(
    organisation_id: int,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    db_organisation = organisation.Organisation.by_id(organisation_id, session)
    db_organisation.delete(session)

    return utils.format_json_response(
        db_organisation, headers, response_model=organisation.OrganisationRead
    )
