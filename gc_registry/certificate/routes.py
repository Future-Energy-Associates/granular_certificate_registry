from pathlib import Path

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session

from gc_registry.account.services import get_account_by_id
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
    GranularCertificateCancelStorage,
    GranularCertificateImportResponse,
    GranularCertificateQuery,
    GranularCertificateQueryRead,
    GranularCertificateTransfer,
    IssuanceMetaDataBase,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import CertificateActionType, UserRoles
from gc_registry.core.services import create_bundle_hash
from gc_registry.device.models import Device
from gc_registry.device.services import (
    get_device_by_local_identifier,
    map_device_to_certificate_read,
)
from gc_registry.logging_config import logger
from gc_registry.user.models import User
from gc_registry.user.validation import validate_user_access, validate_user_role
from gc_registry.utils import parse_import_file

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


@router.get("/certificate_import_template", response_class=FileResponse)
def get_import_template(current_user: User = Depends(get_current_user)):
    """Return a template CSV file for importing GC bundles."""
    template_path = (
        Path(__file__).parent.parent / "static" / "templates" / "gc_import_template.csv"
    )

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")

    return FileResponse(
        path=template_path,
        filename="gc_import_template.csv",
        media_type="text/csv",
    )


@router.post(
    "/import",
    response_model=GranularCertificateImportResponse,
    status_code=201,
)
async def import_certificate_bundle(
    account_id: int = Form(...),
    file: UploadFile = File(...),
    device_json: str = Form(...),
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> GranularCertificateImportResponse:
    """Simplified implementation of import functionality for GC bundles into GCOS.

    This endpoint accepts a CSV or JSON file containing GC bundles and imports them into the database,
    associating them with a generic import device and account as defined in `seed.py`.

    The device_json parameters should be provided in the following contexts:
    - Device not present on GCOS, first time importing for this device: full details must be provided
    - Device not present on GCOS, but not the first time importing for this device: only the device name must be provided
    - Device present on GCOS: only the device name must be provided

    Supported file formats:
    - CSV: Standard comma-separated values with headers
    - JSON: Array of objects format, e.g., [{"column1": "value1", "column2": "value2"}, ...]

    It is assumed that the device that originally was issued the GC bundles is not present
    on GCOS - an instance of the device will be created from the import file data provided
    but linked to a generic import account that is inaccessible to users.

    To prevent double counting, we also assume that the GC bundles are issued according
    to the EnergyTag Standard, and as such, will have a unique issuance ID associated
    with the originating device and a consistent set of bundle range start and end IDs.

    Example request structure using a CSV file through Python:

    device_data = {
        "device_name": "Solar Farm 1",
        "local_device_identifier": "SF001",
        "grid": "ERCOT",
        "energy_source": "solar_pv",
        "technology_type": "photovoltaic",
        "operational_date": "2020-01-01",
        "power_mw": 50.0,
        "location": "Texas, USA",
        "is_storage": False
    }

    with open('path/to/certificates.csv', 'rb') as file:
        files = {
            'file': ('certificates.csv', file, 'text/csv')
        }

        data = {
            'account_id': 123,
            'device_json': json.dumps(device_data)  # Note: no extra nesting needed here
        }

        response = requests.post(
            'http://your-api-url/import',
            files=files,
            data=data,
            headers={
                'Authorization': f'Bearer {your-jwt-token}'
            }
        )

    Args:
        account_id (int): The ID of the account to import the GCs to.
        file (UploadFile): The CSV or JSON file containing the GCs to import.
        device_json (str): JSON string containing device details to import the GCs to.

    Returns:
        GranularCertificateImportResponse: Information on the imported GC bundles and issuance metadata.
    """
    validate_user_role(current_user, required_role=UserRoles.STORAGE_VALIDATOR)

    account = get_account_by_id(int(account_id), read_session)
    if not account:
        raise HTTPException(
            status_code=404, detail=f"Account with ID {account_id} not found."
        )
    validate_user_access(current_user, account.id, read_session)

    try:
        # Read the uploaded file
        contents = await file.read()
        content_str = contents.decode("utf-8")

        # Parse the file into a pandas DataFrame
        gc_df = parse_import_file(file.filename, content_str)

        gc_bundles = services.import_gc_bundles(
            account_id, gc_df, device_json, write_session, read_session, esdb_client
        )

        return GranularCertificateImportResponse(
            message="Certificate bundles imported successfully.",
            number_of_imported_certificate_bundles=len(gc_bundles),
            total_imported_energy=sum(bundle.bundle_quantity for bundle in gc_bundles),
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/transfer",
    response_model=GranularCertificateActionRead,
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

        query_dict = certificate_bundle_query.model_dump()

        if certificate_bundles_from_query is not None:
            granular_certificate_bundles_read = [
                GranularCertificateBundleRead.model_validate(certificate.model_dump())
                for certificate in certificate_bundles_from_query
            ]
        else:
            granular_certificate_bundles_read = []

        query_dict["granular_certificate_bundles"] = granular_certificate_bundles_read

        certificate_query = GranularCertificateQueryRead.model_validate(query_dict)

    except Exception as e:
        logger.error(f"Error querying GCs: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    return certificate_query


@router.post(
    "/query_full",
    response_model=list[GranularCertificateBundleReadFull],
    status_code=202,
)
def query_certificate_bundles_full_route(
    certificate_bundle_query: GranularCertificateQuery,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Return all certificates from the specified Account that match the provided search criteria,
    including the full view of the certificate bundle, issuance metadata, and device."""

    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)
    validate_user_access(current_user, certificate_bundle_query.source_id, read_session)

    certificate_bundles_from_query = services.query_certificate_bundles(
        certificate_bundle_query, read_session
    )

    if not certificate_bundles_from_query:
        return []

    # Get unique metadata and device IDs
    metadata_ids = {
        certificate.metadata_id for certificate in certificate_bundles_from_query
    }
    device_ids = {
        certificate.device_id for certificate in certificate_bundles_from_query
    }

    issuance_metadata_dicts = {}
    device_dicts = {}

    for metadata_id in metadata_ids:
        issuance_metadata = IssuanceMetaData.by_id(metadata_id, read_session)
        if not issuance_metadata:
            raise HTTPException(
                status_code=404,
                detail="Issuance metadata not found for certificate bundle",
            )
        issuance_metadata_dicts[metadata_id] = issuance_metadata.model_dump()

    for device_id in device_ids:
        device = Device.by_id(device_id, read_session)
        device_dicts[device_id] = map_device_to_certificate_read(device)

    certificate_bundle_fulls = []
    for certificate in certificate_bundles_from_query:
        certificate_bundle_full = (
            certificate.model_dump()
            | issuance_metadata_dicts[certificate.metadata_id]
            | device_dicts[certificate.device_id]
        )
        certificate_bundle_full["id"] = certificate.id
        certificate_bundle_fulls.append(certificate_bundle_full)

    return certificate_bundle_fulls


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
    certificate_bundle_full["id"] = certificate_bundle.id

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

        certificate_action_read = services.process_certificate_bundle_action(
            certificate_cancel, write_session, read_session, esdb_client
        )

        return certificate_action_read
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/cancel_for_storage",
    response_model=GranularCertificateActionRead,
    status_code=202,
)
def certificate_bundle_cancellation_for_storage(
    certificate_cancel: GranularCertificateCancelStorage,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Cancel a fixed number of certificates matched to the given filter parameters within the specified Account."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, certificate_cancel.source_id, read_session)

    storage_device = get_device_by_local_identifier(
        read_session, certificate_cancel.storage_local_device_identifier
    )

    print(f"Storage device: {storage_device}")

    if not storage_device:
        raise HTTPException(
            status_code=404,
            detail=f"Storage device not found for the provided local identifier: {certificate_cancel.storage_local_device_identifier}",
        )

    db_certificate_action = services.process_certificate_bundle_action(
        certificate_cancel, write_session, read_session, esdb_client
    )

    return db_certificate_action


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
