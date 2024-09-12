from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.authentication import services
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import GranularCertificateBundleBase
from gc_registry.database import db
from gc_registry.storage.models import (
    StorageAction,
    StorageChargeRecord,
    StorageDischargeRecord,
)
from gc_registry.storage.schemas import (
    SCRQueryResponse,
    SDRQueryResponse,
    StorageActionResponse,
    StorageChargeRecordBase,
    StorageDischargeRecordBase,
)

# Router initialisation
router = APIRouter(tags=["Storage"])


@router.post(
    "/storage/create_scr",
    response_model=StorageChargeRecord,
    status_code=200,
)
def create_SCR(
    scr: StorageChargeRecordBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Create a Storage Charge Record with the specified properties."""
    db_scr = StorageChargeRecord.create(scr, session)

    return utils.format_json_response(
        db_scr,
        headers,
        response_model=StorageChargeRecord,
    )


@router.get(
    "/storage/query_scr",
    response_model=SCRQueryResponse,
    status_code=200,
)
def query_SCR(
    scr_query: StorageAction,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Return all SCRs from the specified Account that match the provided search criteria."""
    scr_action = StorageAction.create(scr_query, session)

    return utils.format_json_response(
        scr_action,
        headers,
        response_model=SCRQueryResponse,
    )


# create storage discharge record
@router.post(
    "/storage/create_sdr",
    response_model=StorageDischargeRecord,
    status_code=200,
    name="Create SDR",
)
def create_SDR(
    sdr: StorageDischargeRecordBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Create a Storage Discharge Record with the specified properties."""
    db_sdr = StorageDischargeRecord.create(sdr, session)

    return utils.format_json_response(
        db_sdr,
        headers,
        response_model=StorageDischargeRecord,
    )


@router.get(
    "/storage/query_sdr",
    response_model=SDRQueryResponse,
    status_code=200,
)
def query_SDR(
    sdr_query: StorageAction,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Return all SDRs from the specified Account that match the provided search criteria."""
    sdr_action = StorageAction.create(sdr_query, session)

    return utils.format_json_response(
        sdr_action,
        headers,
        response_model=SDRQueryResponse,
    )


@router.post(
    "/storage/withdraw_scr",
    response_model=StorageActionResponse,
    status_code=200,
)
def SCR_withdraw(
    storage_action_base: StorageAction,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """(Issuing Body only) - Withdraw a fixed number of SCRs from the specified Account matching the provided search criteria."""
    scr_action = StorageAction.create(storage_action_base, session)

    return utils.format_json_response(
        scr_action,
        headers,
        response_model=StorageActionResponse,
    )


@router.post(
    "/storage/withdraw_sdr",
    response_model=StorageActionResponse,
    status_code=200,
)
def SDR_withdraw(
    storage_action_base: StorageAction,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """(Issuing Body only) - Withdraw a fixed number of SDRs from the specified Account matching the provided search criteria."""
    sdr_action = StorageAction.create(storage_action_base, session)

    return utils.format_json_response(
        sdr_action,
        headers,
        response_model=StorageActionResponse,
    )


@router.patch(
    "/storage/update_mutables",
    response_model=StorageActionResponse,
    status_code=200,
)
def update_storage_mutables(
    storage_update: StorageAction,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Update the mutable aspects (associated Account ID, status) of a given certificate bundle."""
    storage_update_action = StorageAction.create(storage_update, session)

    return utils.format_json_response(
        storage_update_action,
        headers,
        response_model=StorageActionResponse,
    )


@router.post(
    "/storage/issue_sdgc",
    response_model=GranularCertificateBundle,
    status_code=200,
)
def issue_SDGC(
    sdgc: GranularCertificateBundleBase,
    headers: dict = Depends(services.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """A GC Bundle that has been issued following the verification of a cancelled GC Bundle and the proper allocation of a pair
    of Storage Charge and Discharge Records. The GC Bundle is issued to the Account of the Storage Device, and is identical to
    a GC Bundle issued to a production Device albeit with additional storage-specific attributes as described in the Standard.

    These bundles can be queried using the same GC Bundle query endpoint as regular GC Bundles, but with the additional option to filter
    by the storage_id and the discharging_start_datetime, which is inherited from the allocated SDR.
    """

    db_sdgc = GranularCertificateBundle.create(sdgc, session)

    return utils.format_json_response(
        db_sdgc,
        headers,
        response_model=GranularCertificateBundle,
    )
