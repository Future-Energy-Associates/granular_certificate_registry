from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import (
    GranularCertificateBundleCreate,
)
from gc_registry.core.database import db, events
from gc_registry.storage.models import (
    StorageAction,
    StorageRecord,
)
from gc_registry.storage.schemas import (
    AllocatedStorageRecordSubmissionResponse,
    StorageActionResponse,
    StorageRecordBase,
    StorageRecordQueryResponse,
)
from gc_registry.user.models import User

# Router initialisation
router = APIRouter(tags=["Storage"])


@router.post(
    "/create_scr",
    response_model=StorageRecordBase,
    status_code=201,
)
def create_SCR(
    scr_base: StorageRecord,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Create a Storage Charge Record with the specified properties."""
    scr = StorageRecord.create(scr_base, write_session, read_session, esdb_client)

    return scr


@router.get(
    "/query_scr",
    response_model=StorageRecordQueryResponse,
    status_code=200,
)
def query_SCR(
    scr_query: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Return all SCRs from the specified Account that match the provided search criteria."""
    scr_action = StorageAction.create(
        scr_query, write_session, read_session, esdb_client
    )

    return scr_action


@router.post(
    "/create_sdr",
    response_model=StorageRecord,
    status_code=201,
)
def create_SDR(
    sdr_base: StorageRecordBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Create a Storage Discharge Record with the specified properties."""
    sdr = StorageRecord.create(sdr_base, write_session, read_session, esdb_client)

    return sdr


@router.get(
    "/query_sdr",
    response_model=AllocatedStorageRecordSubmissionResponse,
    status_code=200,
)
def query_SDR(
    sdr_query: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Return all SDRs from the specified Account that match the provided search criteria."""
    sdr_action = StorageAction.create(
        sdr_query, write_session, read_session, esdb_client
    )

    return sdr_action


@router.post(
    "/withdraw_scr",
    response_model=StorageActionResponse,
    status_code=200,
)
def SCR_withdraw(
    storage_action_base: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """(Issuing Body only) - Withdraw a fixed number of SCRs from the specified Account matching the provided search criteria."""
    scr_action = StorageAction.create(
        storage_action_base, write_session, read_session, esdb_client
    )

    return scr_action


@router.post(
    "/withdraw_sdr",
    response_model=StorageActionResponse,
    status_code=200,
)
def SDR_withdraw(
    storage_action_base: StorageAction,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """(Issuing Body only) - Withdraw a fixed number of SDRs from the specified Account matching the provided search criteria."""
    sdr_action = StorageAction.create(
        storage_action_base, write_session, read_session, esdb_client
    )

    return sdr_action


@router.post(
    "/issue_sdgc",
    response_model=GranularCertificateBundle,
    status_code=200,
)
def issue_SDGC(
    sdgc_create: GranularCertificateBundleCreate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """A GC Bundle that has been issued following the verification of a cancelled GC Bundle and the proper allocation of a pair
    of Storage Charge and Discharge Records. The GC Bundle is issued to the Account of the Storage Device, and is identical to
    a GC Bundle issued to a production Device albeit with additional storage-specific attributes as described in the Standard.

    These bundles can be queried using the same GC Bundle query endpoint as regular GC Bundles, but with the additional option to filter
    by the storage_id and the discharging_start_datetime, which is inherited from the allocated SDR.
    """

    sdgc = GranularCertificateBundle.create(
        sdgc_create, write_session, read_session, esdb_client
    )

    return sdgc
