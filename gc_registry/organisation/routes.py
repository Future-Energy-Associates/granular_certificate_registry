from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.core.database import db, events
from gc_registry.organisation import models

# Router initialisation
router = APIRouter(tags=["Organisations"])


# organisation
@router.post("/create", response_model=models.OrganisationRead)
def create_organisation(
    organisation_base: models.OrganisationBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    organisation = models.Organisation.create(
        organisation_base, write_session, read_session, esdb_client
    )

    return organisation


@router.get("/{organisation_id}", response_model=models.OrganisationRead)
def read_organisation(
    organisation_id: int,
    read_session: Session = Depends(db.get_read_session),
):
    organisation = models.Organisation.by_id(organisation_id, read_session)

    return organisation


@router.patch("/update/{organisation_id}", response_model=models.OrganisationRead)
def update_organisation(
    organisation_id: int,
    organisation_update: models.OrganisationUpdate,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    organisation = models.Organisation.by_id(organisation_id, read_session)

    return organisation.update(
        organisation_update, write_session, read_session, esdb_client
    )


@router.delete("/delete/{organisation_id}", response_model=models.OrganisationRead)
def delete_organisation(
    organisation_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    organisation = models.Organisation.by_id(organisation_id, write_session)
    return organisation.delete(write_session, read_session, esdb_client)
