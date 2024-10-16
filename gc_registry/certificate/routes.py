from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from gc_registry.certificate.models import (
    GranularCertificateAction,
    GranularCertificateBundle,
)
from gc_registry.certificate.schemas import (
    GranularCertificateActionRead,
    GranularCertificateBundleBase,
)
from gc_registry.certificate.services import create_bundle_hash
from gc_registry.core.database import db, events

# Router initialisation
router = APIRouter(tags=["Certificates"])


@router.post(
    "/create",
    response_model=GranularCertificateBundle,
    status_code=201,
)
def create_certificate_bundle(
    certificate_bundle: GranularCertificateBundleBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
    nonce: str = None,
):
    """Create a GC Bundle with the specified properties."""

    # Bundle issuance ID is the unique combination of device ID,
    # energy carrier, and production starting interval.
    # certificate_bundle.issuance_id = f"{certificate_bundle.device_id}-{certificate_bundle.production_starting_interval}"

    # # Bundle hash is the sha256 of the bundle's properties and, if the result of a bundle split,
    # # a nonce taken from the hash of the parent bundle.
    # certificate_bundle.hash = create_bundle_hash(certificate_bundle, nonce)

    db_certificate_bundles = GranularCertificateBundle.create(
        certificate_bundle, write_session, read_session, esdb_client
    )

    if not db_certificate_bundles:
        raise HTTPException(status_code=500, detail="Could not create Account")

    db_certificate_bundle = db_certificate_bundles[0].model_dump()

    return db_certificate_bundle


@router.post(
    "/transfer",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_transfer(
    certificate_bundle_action: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Transfer a fixed number of certificates matched to the given filter parameters to the specified target Account."""

    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.get(
    "/query",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def query_certificate_bundles(
    certificate_bundle_query: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Return all certificates from the specified Account that match the provided search criteria."""
    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_query, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.post(
    "/recurring_transfer",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_recurring_transfer(
    certificate_bundle_action: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Set up a protocol that transfers a fixed number of certificates matching the provided search criteria to a given target Account once per time period."""
    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.post(
    "/cancel",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_cancellation(
    certificate_bundle_action: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Cancel a fixed number of certificates matched to the given filter parameters within the specified Account."""
    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.post(
    "/recurring_cancel",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_recurring_cancellation(
    certificate_bundle_action: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Set up a protocol that cancels a fixed number of certificates matching the provided search criteria within a given Account once per time period."""
    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.post(
    "/claim",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_claim(
    certificate_bundle_action: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Claim a fixed number of cancelled certificates matching the provided search criteria within a given Account,
    if the User is specified as the Beneficiary of those cancelled GCs. For more information on the claim process,
    please see page 15 of the EnergyTag GC Scheme Standard document."""
    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.post(
    "/withdraw",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_withdraw(
    certificate_bundle_action: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """(Issuing Body only) - Withdraw a fixed number of certificates from the specified Account matching the provided search criteria."""
    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.post(
    "/reseve",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_reserve(
    certificate_bundle_action: GranularCertificateAction,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Label a fixed number of certificates as Reserved from the specified Account matching the provided search criteria."""
    db_certificate_action = GranularCertificateAction.create(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action
