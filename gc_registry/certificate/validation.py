from typing import Any

from fluent_validator import validate  # type: ignore
from sqlmodel import Session

from gc_registry.certificate.models import (
    GranularCertificateBundle,
)
from gc_registry.certificate.schemas import GranularCertificateBundleCreate
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.models import Device
from gc_registry.device.services import (
    device_mw_capacity_to_wh_max,
    get_device_capacity_by_id,
)
from gc_registry.settings import settings


def verifiy_bundle_lineage(
    granular_certificate_bundle_parent: GranularCertificateBundle,
    granular_certificate_bundle_child: GranularCertificateBundle,
):
    """
    Given a parent and child GC Bundle, verify that the child's hash
    can be recreated from the parent's hash and the child's nonce.

    Args:
        granular_certificate_bundle_parent (GranularCertificateBundle): The parent GC Bundle
        granular_certificate_bundle_child (GranularCertificateBundle): The child GC Bundle

    Returns:
        bool: Whether the child's hash can be recreated from the parent's hash
    """

    return (
        create_bundle_hash(
            granular_certificate_bundle_child, granular_certificate_bundle_parent.hash
        )
        == granular_certificate_bundle_child.hash
    )


def validate_granular_certificate_bundle(
    db_session: Session,
    raw_granular_certificate_bundle: dict[str, Any],
    is_storage_device: bool,
    max_certificate_id: int,
    hours: float = settings.CERTIFICATE_GRANULARITY_HOURS,
) -> GranularCertificateBundle:
    granular_certificate_bundle = GranularCertificateBundleCreate.model_validate(
        raw_granular_certificate_bundle
    )

    device_id = granular_certificate_bundle.device_id

    device_mw = get_device_capacity_by_id(db_session, device_id)

    if not device_mw:
        raise ValueError(f"Device with ID {device_id} not found")

    # device_mw = device_w / W_IN_MW
    device_max_watts_hours = device_mw_capacity_to_wh_max(device_mw, hours)

    # Validate the bundle quantity is equal to the difference between the bundle ID range
    # and less than the device max watts hours
    validate(
        granular_certificate_bundle.bundle_quantity, identifier="bundle_quantity"
    ).less_than(device_max_watts_hours * settings.CAPACITY_MARGIN).equal(
        granular_certificate_bundle.certificate_bundle_id_range_end
        - granular_certificate_bundle.certificate_bundle_id_range_start
        + 1
    )

    # Validate the bundle ID range start is greater than the previous max certificate ID
    validate(
        granular_certificate_bundle.certificate_bundle_id_range_start,
        identifier="certificate_bundle_id_range_start",
    ).equal(max_certificate_id + 1)

    # At this point if integrating wtih EAC registry or possibility of cross registry transfer
    # add integrations with external sources for further validation e.g. cancellation of underlying EACs

    if is_storage_device:
        # TODO: add additional storage validation
        pass

    return GranularCertificateBundle.model_validate(
        granular_certificate_bundle.model_dump()
    )


def validate_imported_granular_certificate_bundle(
    raw_granular_certificate_bundle: dict[str, Any],
    existing_bundles: list[GranularCertificateBundle],
    import_device: Device,
    hours: float = settings.CERTIFICATE_GRANULARITY_HOURS,
):
    """Validate a granular certificate bundle imported from another registry.

    The validation process is different from the internal issuance process in that
    we cannot assume continuity of the range IDs as the original issuance will have
    taken place in a different registry.

    The validation process is therefore:
    - Assert that the import device capacity is consistent with the bundle data
    - Validation on the bundle range IDs in isolation
    - Check that the imported bundle does not overlap with existing bundles for that import
    device

    Args:
        raw_granular_certificate_bundle (dict[str, Any]): The raw bundle data
        existing_bundles (list[GranularCertificateBundle]): The existing bundles for the import device
        import_device (Device): The import device
        hours (float): The hours in the certificate granularity
    """

    granular_certificate_bundle = GranularCertificateBundleCreate.model_validate(
        raw_granular_certificate_bundle
    )

    device_max_watts_hours = device_mw_capacity_to_wh_max(import_device.power_mw, hours)

    # Validate the bundle quantity is equal to the difference between the bundle ID range
    # and less than the device max watts hours
    validate(
        granular_certificate_bundle.bundle_quantity, identifier="bundle_quantity"
    ).less_than(device_max_watts_hours * settings.CAPACITY_MARGIN).equal(
        granular_certificate_bundle.certificate_bundle_id_range_end
        - granular_certificate_bundle.certificate_bundle_id_range_start
        + 1
    )

    # Check that the imported bundle does not overlap with existing bundles for that import device
    for existing_bundle in existing_bundles:
        new_start = granular_certificate_bundle.certificate_bundle_id_range_start
        new_end = granular_certificate_bundle.certificate_bundle_id_range_end
        existing_start = existing_bundle.certificate_bundle_id_range_start
        existing_end = existing_bundle.certificate_bundle_id_range_end

        overlap_detected = (
            # New start overlaps with existing range (new_start between existing_start and existing_end)
            (new_start >= existing_start and new_start <= existing_end)
            or
            # New end overlaps with existing range (new_end between existing_start and existing_end)
            (new_end >= existing_start and new_end <= existing_end)
            or
            # New range completely contains existing range
            (new_start <= existing_start and new_end >= existing_end)
            or
            # Existing range completely contains new range
            (existing_start <= new_start and existing_end >= new_end)
        )

        if overlap_detected:
            raise ValueError(
                f"""Imported bundle range [{new_start}, {new_end}] for issuance ID \
                    {granular_certificate_bundle.issuance_id} overlaps with existing bundle \
                    {existing_bundle.id} range [{existing_start}, {existing_end}]"""
            )
