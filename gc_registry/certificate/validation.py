from typing import Any

from fastapi import HTTPException
from fluent_validator import validate  # type: ignore
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.certificate.models import (
    GranularCertificateAction,
    GranularCertificateBundle,
)
from gc_registry.certificate.schemas import GranularCertificateBundleCreate
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.services import (
    device_mw_capacity_to_wh_max,
    get_device_capacity_by_id,
)
from gc_registry.settings import settings
from gc_registry.user.models import User


def verifiy_bundle_lineage(
    gc_bundle_parent: GranularCertificateBundle,
    gc_bundle_child: GranularCertificateBundle,
):
    """
    Given a parent and child GC Bundle, verify that the child's hash
    can be recreated from the parent's hash and the child's nonce.

    Args:
        gc_bundle_parent (GranularCertificateBundle): The parent GC Bundle
        gc_bundle_child (GranularCertificateBundle): The child GC Bundle

    Returns:
        bool: Whether the child's hash can be recreated from the parent's hash
    """

    return (
        create_bundle_hash(gc_bundle_child, gc_bundle_parent.hash)
        == gc_bundle_child.hash
    )


def validate_granular_certificate_bundle(
    db_session: Session,
    raw_gcb: dict[str, Any],
    is_storage_device: bool,
    max_certificate_id: int,
    hours: float = settings.CERTIFICATE_GRANULARITY_HOURS,
) -> GranularCertificateBundle:
    gcb = GranularCertificateBundleCreate.model_validate(raw_gcb)

    W_IN_MW = 1e6
    device_id = gcb.device_id

    device_w = get_device_capacity_by_id(db_session, device_id)

    if not device_w:
        raise ValueError(f"Device with ID {device_id} not found")

    device_mw = device_w / W_IN_MW
    device_max_watts_hours = device_mw_capacity_to_wh_max(device_mw, hours)

    # Validate the bundle quantity is equal to the difference between the bundle ID range
    # and less than the device max watts hours
    validate(gcb.bundle_quantity, identifier="bundle_quantity").less_than(
        device_max_watts_hours * settings.CAPACITY_MARGIN
    ).equal(gcb.bundle_id_range_end - gcb.bundle_id_range_start + 1)

    # Validate the bundle ID range start is greater than the previous max certificate ID
    validate(gcb.bundle_id_range_start, identifier="bundle_id_range_start").equal(
        max_certificate_id + 1
    )

    # At this point if integrating wtih EAC registry or possibility of cross registry transfer
    # add integrations with external sources for further validation e.g. cancellation of underlying EACs

    if is_storage_device:
        # TODO: add additional storage validation
        pass

    return GranularCertificateBundle.model_validate(gcb.model_dump())


def validate_user_access(
    granular_certificate_action: GranularCertificateAction, read_session: Session
):
    """
    Validate that the user's role allows it to perform the requested action.

    Args:
        granular_certificate_action (GranularCertificateAction): The action to validate

    Raises:
        HTTPException: If the user action is rejected, return a 403 with the reason for rejection.
    """

    # Get the user's info
    user = User.by_id(granular_certificate_action.user_id, read_session).role

    # Assert that the user has access to the source account
    if granular_certificate_action.source_id not in user.account_ids:
        msg = "User does not have access to the specified source account"
        raise HTTPException(status_code=403, detail=msg)
