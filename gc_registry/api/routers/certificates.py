# Imports
import os

from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.api import utils
from gc_registry.api.routers import authentication
from gc_registry.datamodel import db
from gc_registry.datamodel.schemas import gc_entities

environment = os.getenv("ENVIRONMENT")


# Router initialisation
router = APIRouter(tags=["Certificates"])


@router.post(
    "/certificates/create",
    response_model=gc_entities.GranularCertificateBundle,
    status_code=201,
)
def create_certificate_bundle(
    certificate_bundle: gc_entities.GranularCertificateBundleBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Create a GC Bundle with the specified properties."""
    db_certificate_bundle = gc_entities.GranularCertificateBundle.create(
        certificate_bundle, session
    )

    return utils.format_json_response(
        db_certificate_bundle,
        headers,
        response_model=gc_entities.GranularCertificateBundle,
    )


@router.post(
    "/certificates/transfer",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=202,
)
def certificate_bundle_transfer(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Transfer a fixed number of certificates matched to the given filter parameters to the specified target Account."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )


@router.get(
    "/certificates/query",
    response_model=gc_entities.GranularCertificateQueryResponse,
    status_code=202,
)
def query_certificate_bundles(
    certificate_bundle_query: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Return all certificates from the specified Account that match the provided search criteria."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_query, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateQueryResponse,
    )


@router.post(
    "/certificates/recurring_transfer",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=202,
)
def certificate_bundle_recurring_transfer(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Set up a protocol that transfers a fixed number of certificates matching the provided search criteria to a given target Account once per time period."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )


@router.post(
    "/certificates/cancel",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=202,
)
def certificate_bundle_cancellation(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Cancel a fixed number of certificates matched to the given filter parameters within the specified Account."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )


@router.post(
    "/certificates/recurring_cancel",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=202,
)
def certificate_bundle_recurring_cancellation(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Set up a protocol that cancels a fixed number of certificates matching the provided search criteria within a given Account once per time period."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )


@router.post(
    "/certificates/claim",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=202,
)
def certificate_bundle_claim(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Claim a fixed number of cancelled certificates matching the provided search criteria within a given Account,
    if the User is specified as the Beneficiary of those cancelled GCs. For more information on the claim process,
    please see page 15 of the EnergyTag GC Scheme Standard document."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )


@router.post(
    "/certificates/withdraw",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=202,
)
def certificate_bundle_withdraw(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """(Issuing Body only) - Withdraw a fixed number of certificates from the specified Account matching the provided search criteria."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )


@router.patch(
    "/certificates/update_mutables",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=201,
)
def update_certificate_mutables(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Update the mutable aspects (associated Account ID, status) of a given certificate bundle."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )


############## Additions for Standard V2 ##############


@router.post(
    "/certificates/reseve",
    response_model=gc_entities.GranularCertificateActionResponse,
    status_code=202,
)
def certificate_bundle_reserve(
    certificate_bundle_action: gc_entities.GranularCertificateAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Label a fixed number of certificates as Reserved from the specified Account matching the provided search criteria."""
    db_certificate_action = gc_entities.GranularCertificateAction.create(
        certificate_bundle_action, session
    )

    return utils.format_json_response(
        db_certificate_action,
        headers,
        response_model=gc_entities.GranularCertificateActionResponse,
    )
