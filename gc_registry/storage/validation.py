import pandas as pd
from sqlmodel import Session, desc, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.account.services import get_accounts_by_user_id
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.core.models.base import UserRoles
from gc_registry.device.services import get_devices_by_account_id
from gc_registry.settings import settings
from gc_registry.storage.models import AllocatedStorageRecord, StorageRecord
from gc_registry.storage.utils import get_storage_records_by_device_id
from gc_registry.user.models import User


def get_latest_storage_record_by_device_id(
    device_id: int,
    read_session: Session,
) -> StorageRecord | None:
    """Retrieve the latest Storage Record for the specified device."""

    # Query the database for the latest allocated storage record for the specified device
    query: SelectOfScalar = (
        select(StorageRecord)
        .where(
            StorageRecord.device_id == device_id,
        )
        .order_by(desc(StorageRecord.flow_start_datetime))
        .limit(1)
    )

    latest_record = read_session.exec(query).first()

    return latest_record


def validate_storage_records(
    measurement_df: pd.DataFrame, read_session: Session, device_id: int
) -> tuple[bool, str | None]:
    """
    Validate the storage records DataFrame to ensure it meets the required data structure.

    # 1 Check the DataFrame is not empty
    # 2 Check required columns are present based on the StorageRecord schema
    # 3 Validate the timestamp columns can be parsed
    # 4 Validate that it is a continuous time series and does not contain gaps or duplicates
    # 5 Validate that the time-series follows the previous time-series aalready stored in the database
    # 6 Validate that the values are within expected ranges relative to the device
    # 7 Validate that there are no duplicate device_id/timestamp combinations alreading in the database

    Args:
        measurement_df (pd.DataFrame): The DataFrame containing storage records.
        read_session (Session): The SQLAlchemy session for reading from the database.
        device_id (int): The ID of the device for which the records are being validated.
    Returns:
        tuple[bool, str | None]: A tuple where the first element is a boolean indicating
                                  whether the validation passed, and the second element is
                                  an error message if validation failed, or None if it passed.
    """

    if measurement_df.empty:
        return False, "Measurement DataFrame is empty."

    if not all(
        col in measurement_df.columns
        for col in ["flow_start_datetime", "flow_end_datetime", "flow_energy"]
    ):
        return False, "Measurement DataFrame is missing required columns."

    # Check if timestamp columns can be parsed into UTC datetime
    try:
        measurement_df["flow_start_datetime"] = pd.to_datetime(
            measurement_df["flow_start_datetime"], utc=True
        )
        measurement_df["flow_end_datetime"] = pd.to_datetime(
            measurement_df["flow_end_datetime"], utc=True
        )
    except Exception as e:
        return False, f"Error parsing datetime columns: {str(e)}"

    # Check for continuous time series
    measurement_df.sort_values(by="flow_start_datetime", inplace=True)
    unique_diff = measurement_df["flow_start_datetime"].diff().dropna().unique()
    if len(unique_diff) != 1 or unique_diff[0] != pd.Timedelta(
        hours=settings.CERTIFICATE_GRANULARITY_HOURS
    ):
        return (
            False,
            "Measurement DataFrame does not have a continuous time series with correct intervals.",
        )

    # Check for duplicates in the time series
    if measurement_df["flow_start_datetime"].duplicated().any():
        return False, "Measurement DataFrame contains duplicate timestamps."

    # get the last stored record for the device
    last_record = get_latest_storage_record_by_device_id(
        device_id=device_id, read_session=read_session
    )

    # check the delta between the last record and the first record in the measurement_df is equal to the expected granularity
    if last_record is not None:
        last_record_time = last_record.flow_start_datetime
        first_measurement_time = measurement_df["flow_start_datetime"].iloc[0]
        expected_delta = pd.Timedelta(hours=settings.CERTIFICATE_GRANULARITY_HOURS)

        if first_measurement_time - last_record_time != expected_delta:
            return (
                False,
                "Measurement DataFrame does not follow the previous time series.",
            )

    # Check that time stamps for this device are not already in the database
    existing_records = get_storage_records_by_device_id(
        device_id,
        read_session,
        start_datetime=measurement_df["flow_start_datetime"].min(),
        end_datetime=measurement_df["flow_start_datetime"].max(),
    )
    if existing_records:
        return (
            False,
            "Measurement DataFrame contains timestamps that already exist in the database.",
        )

    measurement_df["flow_start_datetime"] = measurement_df[
        "flow_start_datetime"
    ].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    measurement_df["flow_end_datetime"] = measurement_df[
        "flow_end_datetime"
    ].dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    return True, None


def validate_allocated_records(
    allocation_record: pd.Series, sdr: pd.Series, scr: pd.Series
):
    if sdr["is_charging"] or not scr["is_charging"]:
        raise ValueError(
            f"Invalid flow types for the specified allocation IDs : \
                            {allocation_record['sdr_allocation_id']} and {allocation_record['scr_allocation_id']}"
        )

    if sdr["flow_start_datetime"] < scr["flow_end_datetime"]:
        raise ValueError(
            f"SDR flow start datetime is after SCR flow end datetime: \
                            {allocation_record['sdr_allocation_id']} and {allocation_record['scr_allocation_id']}"
        )

    return


def validate_allocated_records_against_gc_bundles(
    allocated_storage_records: list[AllocatedStorageRecord],
    charge_records: list[StorageRecord],
    gc_bundles: list[GranularCertificateBundle],
):
    """Given a list of allocated storage records, verify that the linked GC
    Bundles sufficient quantities and datetimes to cover the allocated storage records.

    Args:
        allocated_storage_records (list[AllocatedStorageRecord]): A list of allocated storage records.
        charge_records (list[StorageRecord]): A list of SCR and SDR records referenced by the allocated storage records.
        gc_bundles (list[GranularCertificateBundle]): A list of GC Bundles.

    Raises:
        ValueError: If the GC Bundles do not have sufficient quantities or datetimes to cover the allocated storage records.
    """

    for allocated_storage_record in allocated_storage_records:
        gc_bundle = next(
            (
                bundle
                for bundle in gc_bundles
                if bundle.id == allocated_storage_record.gc_allocation_id
            ),
            None,
        )

        scr_record = next(
            (
                record
                for record in charge_records
                if record.id == allocated_storage_record.scr_allocation_id
            ),
            None,
        )

        # sdr_record = next(
        #     (
        #         record
        #         for record in charge_records
        #         if record.id == allocated_storage_record.sdr_allocation_id
        #     ),
        #     None,
        # )

        if not gc_bundle:
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} not found"
            )

        if not scr_record:
            raise ValueError(
                f"SCR Record with ID {allocated_storage_record.scr_allocation_id} not found"
            )

        if (
            gc_bundle.bundle_quantity
            != allocated_storage_record.sdr_proportion * scr_record.flow_energy
        ):
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} does not have sufficient quantity"
            )

        if gc_bundle.production_starting_interval < scr_record.flow_start_datetime:
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} does not have sufficient start datetime"
            )

        if gc_bundle.production_starting_interval > scr_record.flow_end_datetime:
            raise ValueError(
                f"GC Bundle with ID {allocated_storage_record.gc_allocation_id} does not have sufficient end datetime"
            )

    return


def validate_access_to_devices(
    device_ids: list[int] | set[int],
    current_user: User,
    read_session: Session,
):
    """Validate that the user has access to the devices associated with the allocated storage records."""

    if isinstance(device_ids, list):
        device_ids = set(device_ids)

    user_accounts = get_accounts_by_user_id(current_user.id, read_session)
    if not user_accounts:
        raise ValueError("User does not have any associated accounts.")

    if current_user.role in [UserRoles.ADMIN, UserRoles.PRODUCTION_USER]:
        user_devices = []
        for account in user_accounts:
            account_devices = get_devices_by_account_id(account.id, read_session)
            user_devices.extend(account_devices)

        user_device_ids = {device.id for device in user_devices}
        if any(device_id not in user_device_ids for device_id in device_ids):
            invalid_devices = device_ids - user_device_ids
            raise PermissionError(
                f"User does not have permission to access devices with IDs {invalid_devices}."
            )
