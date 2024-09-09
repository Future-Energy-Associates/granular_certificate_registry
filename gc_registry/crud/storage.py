import os

from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.crud import authentication
from gc_registry.database import db
from gc_registry.schemas import certificate, storage, storage_action

# Router initialisation
router = APIRouter(tags=["Storage"])


@router.post(
    "/storage/create_scr",
    response_model=storage.StorageChargeRecord,
    status_code=200,
)
def create_SCR(
    scr: storage.StorageChargeRecordBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Create a Storage Charge Record with the specified properties."""
    db_scr = storage.StorageChargeRecord.create(scr, session)

    return utils.format_json_response(
        db_scr,
        headers,
        response_model=storage.StorageChargeRecord,
    )


@router.get(
    "/storage/query_scr",
    response_model=storage_action.SCRQueryResponse,
    status_code=200,
)
def query_SCR(
    scr_query: storage_action.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Return all SCRs from the specified Account that match the provided search criteria."""
    scr_action = storage_action.StorageAction.create(scr_query, session)

    return utils.format_json_response(
        scr_action,
        headers,
        response_model=storage_action.SCRQueryResponse,
    )


# create storage discharge record
@router.post(
    "/storage/create_sdr",
    response_model=storage.StorageDischargeRecord,
    status_code=200,
    name="Create SDR",
)
def create_SDR(
    sdr: storage.StorageDischargeRecordBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Create a Storage Discharge Record with the specified properties."""
    db_sdr = storage.StorageDischargeRecord.create(sdr, session)

    return utils.format_json_response(
        db_sdr,
        headers,
        response_model=storage.StorageDischargeRecord,
    )


@router.get(
    "/storage/query_sdr",
    response_model=storage_action.SDRQueryResponse,
    status_code=200,
)
def query_SDR(
    sdr_query: storage_action.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Return all SDRs from the specified Account that match the provided search criteria."""
    sdr_action = storage_action.StorageAction.create(sdr_query, session)

    return utils.format_json_response(
        sdr_action,
        headers,
        response_model=storage_action.SDRQueryResponse,
    )


@router.post(
    "/storage/withdraw_scr",
    response_model=storage_action.StorageActionResponse,
    status_code=200,
)
def SCR_withdraw(
    storage_action_base: storage_action.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """(Issuing Body only) - Withdraw a fixed number of SCRs from the specified Account matching the provided search criteria."""
    scr_action = storage_action.StorageAction.create(storage_action_base, session)

    return utils.format_json_response(
        scr_action,
        headers,
        response_model=storage_action.StorageActionResponse,
    )


@router.post(
    "/storage/withdraw_sdr",
    response_model=storage_action.StorageActionResponse,
    status_code=200,
)
def SDR_withdraw(
    storage_action_base: storage_action.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """(Issuing Body only) - Withdraw a fixed number of SDRs from the specified Account matching the provided search criteria."""
    sdr_action = storage_action.StorageAction.create(storage_action_base, session)

    return utils.format_json_response(
        sdr_action,
        headers,
        response_model=storage_action.StorageActionResponse,
    )


@router.patch(
    "/storage/update_mutables",
    response_model=storage_action.StorageActionResponse,
    status_code=200,
)
def update_storage_mutables(
    storage_update: storage_action.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Update the mutable aspects (associated Account ID, status) of a given certificate bundle."""
    storage_update_action = storage_action.StorageAction.create(storage_update, session)

    return utils.format_json_response(
        storage_update_action,
        headers,
        response_model=storage_action.StorageActionResponse,
    )


@router.post(
    "/storage/issue_sdgc",
    response_model=certificate.GranularCertificateBundle,
    status_code=200,
)
def issue_SDGC(
    sdgc: certificate.GranularCertificateBundleBase,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """A GC Bundle that has been issued following the verification of a cancelled GC Bundle and the proper allocation of a pair
    of Storage Charge and Discharge Records. The GC Bundle is issued to the Account of the Storage Device, and is identical to
    a GC Bundle issued to a production Device albeit with additional storage-specific attributes as described in the Standard.

    These bundles can be queried using the same GC Bundle query endpoint as regular GC Bundles, but with the additional option to filter
    by the storage_id and the discharging_start_datetime, which is inherited from the allocated SDR.
    """

    db_sdgc = certificate.GranularCertificateBundle.create(sdgc, session)

    return utils.format_json_response(
        db_sdgc,
        headers,
        response_model=certificate.GranularCertificateBundle,
    )
