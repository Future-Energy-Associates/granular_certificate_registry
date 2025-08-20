import datetime

from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord


def get_device_ids_in_allocated_storage_records(read_session: Session) -> list[int]:
    """Retrieve all device IDs that have allocated storage records."""

    # Query the database for unique device IDs in allocated storage records
    device_ids = read_session.exec(
        select(AllocatedStorageRecord.device_id).distinct()
    ).all()

    return list(device_ids)


def get_storage_records_by_device_id(
    device_id: int,
    read_session: Session,
    start_datetime: datetime.datetime | None = None,
    end_datetime: datetime.datetime | None = None,
) -> list[StorageRecord] | None:
    """Retrieve all Storage Records for the specified device."""

    query: SelectOfScalar = select(StorageRecord).where(
        StorageRecord.device_id == device_id,
        ~StorageRecord.is_deleted,
    )

    if start_datetime:
        query = query.where(StorageRecord.flow_start_datetime >= start_datetime)

    if end_datetime:
        query = query.where(StorageRecord.flow_start_datetime <= end_datetime)

    storage_records = read_session.exec(query).all()

    return storage_records


def get_storage_records_by_id(
    storage_record_ids: list[int],
    read_session: Session,
) -> list[StorageRecord] | None:
    """Retrieve a Storage Record by its ID."""

    query: SelectOfScalar = select(StorageRecord).where(
        StorageRecord.id.in_(storage_record_ids),  # type: ignore
        ~StorageRecord.is_deleted,
    )

    storage_records = read_session.exec(query).all()

    return storage_records


def get_storage_record_by_device_id_and_interval(
    read_session: Session,
    device_id: int,
    flow_start_datetime: datetime.date,
) -> StorageRecord | None:
    """Retrieve all Storage Records for the specified device within a date range."""

    # Query the database for storage records for the specified device and time interval
    query: SelectOfScalar = select(StorageRecord).where(
        StorageRecord.device_id == device_id,
        StorageRecord.flow_start_datetime == flow_start_datetime,
        ~StorageRecord.is_deleted,
    )

    storage_record = read_session.exec(query).all()

    if len(storage_record) > 1:
        raise ValueError(
            f"Multiple storage records found for device ID {device_id} and flow start datetime {flow_start_datetime}."
        )

    return storage_record[0] if storage_record else None


def get_allocated_storage_records_by_id(
    allocated_storage_record_ids: list[int],
    read_session: Session,
) -> list[AllocatedStorageRecord] | None:
    """Retrieve an Allocated Storage Record by its ID."""

    query: SelectOfScalar = select(AllocatedStorageRecord).where(
        AllocatedStorageRecord.id.in_(allocated_storage_record_ids),  # type: ignore
        ~AllocatedStorageRecord.is_deleted,
    )

    allocated_storage_records = read_session.exec(query).all()

    return allocated_storage_records


def get_allocated_storage_records_for_storage_record_id(
    read_session: Session,
    storage_record_id: int,
) -> list[AllocatedStorageRecord] | None:
    """Retrieve all Allocated Storage Records for the specified Storage Record ID."""

    # Query the database for allocated storage records for the specified storage record ID
    query: SelectOfScalar = select(AllocatedStorageRecord).where(
        AllocatedStorageRecord.scr_allocation_id
        == storage_record_id | AllocatedStorageRecord.sdr_allocation_id
        == storage_record_id,
        ~AllocatedStorageRecord.is_deleted,
    )

    allocated_storage_records = read_session.exec(query).all()

    return allocated_storage_records


def get_allocated_storage_records_by_device_id(
    device_id: int,
    read_session: Session,
    created_after: datetime.date,
    created_before: datetime.date,
) -> list[AllocatedStorageRecord] | None:
    """Retrieve all Allocated Storage Records for the specified device."""

    # Query the database for allocated storage records for the specified device
    query: SelectOfScalar = select(AllocatedStorageRecord).where(
        AllocatedStorageRecord.device_id == device_id,
        AllocatedStorageRecord.created_at >= created_after,
        AllocatedStorageRecord.created_at < created_before,
    )

    allocated_storage_records = read_session.exec(query).all()

    return allocated_storage_records
