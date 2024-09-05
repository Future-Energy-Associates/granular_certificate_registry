# Imports
import os

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.api import utils
from src.api.routers import authentication
from src import db
from src.schemas import certificate, storage

environment = os.getenv("ENVIRONMENT")

# Router initialisation
router = APIRouter(tags=["Storage"])


### Storage Charge Records ###


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
    response_model=storage.SCRQueryResponse,
    status_code=200,
)
def query_SCR(
    scr_query: storage.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Return all SCRs from the specified Account that match the provided search criteria."""
    scr_action = storage.StorageAction.create(scr_query, session)

    return utils.format_json_response(
        scr_action,
        headers,
        response_model=storage.SCRQueryResponse,
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
    response_model=storage.SDRQueryResponse,
    status_code=200,
)
def query_SDR(
    sdr_query: storage.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Return all SDRs from the specified Account that match the provided search criteria."""
    sdr_action = storage.StorageAction.create(sdr_query, session)

    return utils.format_json_response(
        sdr_action,
        headers,
        response_model=storage.SDRQueryResponse,
    )


@router.post(
    "/storage/withdraw_scr",
    response_model=storage.StorageActionResponse,
    status_code=200,
)
def SCR_withdraw(
    storage_action: storage.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """(Issuing Body only) - Withdraw a fixed number of SCRs from the specified Account matching the provided search criteria."""
    scr_action = storage.StorageAction.create(storage_action, session)

    return utils.format_json_response(
        scr_action,
        headers,
        response_model=storage.StorageActionResponse,
    )


@router.post(
    "/storage/withdraw_sdr",
    response_model=storage.StorageActionResponse,
    status_code=200,
)
def SDR_withdraw(
    storage_action: storage.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """(Issuing Body only) - Withdraw a fixed number of SDRs from the specified Account matching the provided search criteria."""
    sdr_action = storage.StorageAction.create(storage_action, session)

    return utils.format_json_response(
        sdr_action,
        headers,
        response_model=storage.StorageActionResponse,
    )


@router.patch(
    "/storage/update_mutables",
    response_model=storage.StorageActionResponse,
    status_code=200,
)
def update_certificate_mutables(
    certificate_bundle_action: storage.StorageAction,
    headers: dict = Depends(authentication.validate_user_and_get_headers),
    session: Session = Depends(db.db_name_to_client["read"].yield_session),
):
    """Update the mutable aspects (associated Account ID, status) of a given certificate bundle."""
    storage_action = storage.StorageAction.create(certificate_bundle_action, session)

    return utils.format_json_response(
        storage_action,
        headers,
        response_model=storage.StorageActionResponse,
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
    by the storage_device_id and the discharging_start_datetime, which is inherited from the allocated SDR.
    """

    db_sdgc = certificate.GranularCertificateBundle.create(sdgc, session)

    return utils.format_json_response(
        db_sdgc,
        headers,
        response_model=certificate.GranularCertificateBundle,
    )
