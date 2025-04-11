from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.models import (
    GranularCertificateAction,
    GranularCertificateBundle,
    IssuanceMetaData,
)
from gc_registry.certificate.schemas import (
    GranularCertificateActionRead,
    GranularCertificateBundleBase,
    GranularCertificateBundleRead,
    GranularCertificateBundleReadFull,
    GranularCertificateCancel,
    GranularCertificateQuery,
    GranularCertificateQueryRead,
    GranularCertificateTransfer,
    IssuanceMetaDataBase,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import CertificateActionType, UserRoles
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.models import Device
from gc_registry.device.services import map_device_to_certificate_read
from gc_registry.logging_config import logger
from gc_registry.user.models import User
from gc_registry.user.validation import validate_user_access, validate_user_role

from . import services

# Router initialisation
router = APIRouter(tags=["Certificates"])


@router.post(
    "/create",
    response_model=GranularCertificateBundle,
    status_code=201,
)
def create_certificate_bundle(
    certificate_bundle: GranularCertificateBundleBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
    nonce: str | None = None,
):
    """Create a GC Bundle with the specified properties."""
    validate_user_role(current_user, required_role=UserRoles.ADMIN)
    try:
        certificate_bundle.issuance_id = services.create_issuance_id(certificate_bundle)
        certificate_bundle.hash = create_bundle_hash(certificate_bundle, nonce)

        db_certificate_bundles = GranularCertificateBundle.create(
            certificate_bundle, write_session, read_session, esdb_client
        )

        if not db_certificate_bundles:
            raise HTTPException(status_code=400, detail="Could not create GC Bundle")

        db_certificate_bundle = db_certificate_bundles[0].model_dump()

        return db_certificate_bundle
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/create_metadata",
    response_model=IssuanceMetaData,
    status_code=201,
)
def create_issuance_metadata(
    issuance_metadata: IssuanceMetaDataBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Create GC issuance metadata with the specified properties."""
    validate_user_role(current_user, required_role=UserRoles.ADMIN)
    try:
        db_issuance_metadata = IssuanceMetaData.create(
            issuance_metadata, write_session, read_session, esdb_client
        )

        if not db_issuance_metadata:
            raise HTTPException(
                status_code=400, detail="Could not create Issuance Metadata"
            )

        db_issuance_metadata = db_issuance_metadata[0].model_dump()  # type: ignore

        return db_issuance_metadata
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/transfer",
    response_model=GranularCertificateAction,
    status_code=202,
)
def certificate_bundle_transfer(
    certificate_transfer: GranularCertificateTransfer,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Transfer a fixed number of certificates matched to the given filter parameters to the specified target Account."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, certificate_transfer.source_id, read_session)

    try:
        db_certificate_action = services.process_certificate_bundle_action(
            certificate_transfer, write_session, read_session, esdb_client
        )

        return db_certificate_action
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/query",
    response_model=GranularCertificateQueryRead,
    status_code=202,
)
def query_certificate_bundles_route(
    certificate_bundle_query: GranularCertificateQuery,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Return all certificates from the specified Account that match the provided search criteria."""
    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)
    validate_user_access(current_user, certificate_bundle_query.source_id, read_session)

    try:
        certificate_bundles_from_query = services.query_certificate_bundles(
            certificate_bundle_query, read_session
        )

        if not certificate_bundles_from_query:
            raise HTTPException(status_code=404, detail="No certificates found")

        query_dict = certificate_bundle_query.model_dump()

        granular_certificate_bundles_read = [
            GranularCertificateBundleRead.model_validate(certificate.model_dump())
            for certificate in certificate_bundles_from_query
        ]

        query_dict["granular_certificate_bundles"] = granular_certificate_bundles_read

        certificate_query = GranularCertificateQueryRead.model_validate(query_dict)

    except Exception as e:
        logger.error(f"Error querying GCs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    return certificate_query


@router.get("/{id}", response_model=GranularCertificateBundleReadFull)
def read_certificate_bundle(
    id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Return the full view of a given granular certificate bundle by ID."""

    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)

    certificate_bundle = GranularCertificateBundle.by_id(id, read_session)

    if not certificate_bundle:
        raise HTTPException(status_code=404, detail="Certificate bundle not found")
    validate_user_access(current_user, certificate_bundle.account_id, read_session)

    # Merge the issuance metadata into the certificate bundle
    issuance_metadata = IssuanceMetaData.by_id(
        certificate_bundle.metadata_id, read_session
    )

    if not issuance_metadata:
        raise HTTPException(
            status_code=404, detail="Issuance metadata not found for certificate bundle"
        )

    device = Device.by_id(certificate_bundle.device_id, read_session)
    device_dict = map_device_to_certificate_read(device)

    if not device:
        raise HTTPException(
            status_code=404, detail="Device not found for certificate bundle"
        )

    certificate_bundle_full = (
        certificate_bundle.model_dump() | issuance_metadata.model_dump() | device_dict
    )

    return certificate_bundle_full


@router.post(
    "/cancel",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_cancellation(
    certificate_cancel: GranularCertificateCancel,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Cancel a fixed number of certificates matched to the given filter parameters within the specified Account."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, certificate_cancel.source_id, read_session)

    try:
        # If no beneficiary is specified, default to the account holder
        if certificate_cancel.beneficiary is None:
            user_name = User.by_id(certificate_cancel.user_id, read_session).name
            certificate_cancel.beneficiary = f"{user_name}"

        db_certificate_action = services.process_certificate_bundle_action(
            certificate_cancel, write_session, read_session, esdb_client
        )

        return db_certificate_action
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/recurring_transfer",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_recurring_transfer(
    certificate_bundle_action: GranularCertificateAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Set up a protocol that transfers a fixed number of certificates matching the provided search criteria to a given target Account once per time period."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(
        current_user, certificate_bundle_action.source_id, read_session
    )

    try:
        db_certificate_action = GranularCertificateAction.create(
            certificate_bundle_action, write_session, read_session, esdb_client
        )

        return db_certificate_action
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/recurring_cancel",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_recurring_cancellation(
    certificate_bundle_action: GranularCertificateAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Set up a protocol that cancels a fixed number of certificates matching the provided search criteria within a given Account once per time period."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(
        current_user, certificate_bundle_action.source_id, read_session
    )

    try:
        db_certificate_action = GranularCertificateAction.create(
            certificate_bundle_action, write_session, read_session, esdb_client
        )

        return db_certificate_action
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/claim",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_claim(
    certificate_bundle_action: GranularCertificateAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Claim a fixed number of cancelled certificates matching the provided search criteria within a given Account,
    if the User is specified as the Beneficiary of those cancelled GCs. For more information on the claim process,
    please see page 15 of the EnergyTag GC Scheme Standard document."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(
        current_user, certificate_bundle_action.source_id, read_session
    )

    try:
        certificate_bundle_action.action_type = CertificateActionType.CLAIM
        db_certificate_action = services.process_certificate_bundle_action(
            certificate_bundle_action, write_session, read_session, esdb_client
        )

        return db_certificate_action
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/withdraw",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_withdraw(
    certificate_bundle_action: GranularCertificateAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """(Issuing Body only) - Withdraw a fixed number of certificates from the specified Account matching the provided search criteria."""
    validate_user_role(current_user, required_role=UserRoles.ADMIN)

    certificate_bundle_action.action_type = CertificateActionType.WITHDRAW
    db_certificate_action = services.process_certificate_bundle_action(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action


@router.post(
    "/reserve",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_reserve(
    certificate_bundle_action: GranularCertificateAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Label a fixed number of certificates as Reserved from the specified Account matching the provided search criteria."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(
        current_user, certificate_bundle_action.source_id, read_session
    )
    certificate_bundle_action.action_type = CertificateActionType.RESERVE
    db_certificate_action = services.process_certificate_bundle_action(
        certificate_bundle_action, write_session, read_session, esdb_client
    )

    return db_certificate_action
