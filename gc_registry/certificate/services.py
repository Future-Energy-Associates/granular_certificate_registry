from sqlmodel import Session
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import (
    CertificateStatus,
    GranularCertificateBundleBase,
)
from gc_registry.device.services import (
    device_mw_capacity_to_wh_max,
    get_device_capacity_by_id,
)

from fluent_validator import validate


def get_max_certificate_id_by_device_id(db_session: Session, device_id: int):
    """Gets the maximum certificate ID from any bundle for a given device, excluding any withdrawn certificates

    Args:


    """

    stmt = select(max(GranularCertificateBundle.bundle_id_range_end)).where(
        GranularCertificateBundle.device_id == device_id,
        GranularCertificateBundle.certificate_status != CertificateStatus.WITHDRAWN,
    )

    max_certificate_id = db_session.exec(stmt).first()

    return int(max_certificate_id[0])


def validate_granular_certificate_bundle(
    gcb: GranularCertificateBundleBase, is_storage_device: bool
) -> None:

    device_id = gcb.device_id

    device_mw = get_device_capacity_by_id(device_id)
    device_max_watts_hours = device_mw_capacity_to_wh_max(device_mw)

    device_max_certificate_id = get_max_certificate_id_by_device_id(device_id)

    validate(gcb.face_value).less_than(device_max_watts_hours).equals(
        gcb.bundle_id_range_end - gcb.bundle_id_range_start
    )
    validate(gcb.bundle_id_range_start).equals(device_max_certificate_id + 1)

    # At this point if integrating wtih EAC registry or possibility of cross registry transfer
    # add integrations with external sources for further validation e.g. cancellation of underlying EACs

    if is_storage_device:
        # TODO: add additional storage validation
        pass

    return None


def create_granular_certificate_bundle(
    db_session: Session, gcb: GranularCertificateBundleBase
):

    db_session.add(bundle)
    db_session.commit()
    db_session.refresh(bundle)
    return bundle
