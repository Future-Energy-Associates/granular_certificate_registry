from esdbclient import EventStoreDBClient
from fastapi import HTTPException, status
from sqlmodel import Session, delete, func, select
from sqlmodel.sql.expression import SelectOfScalar

from gc_registry.account.models import Account
from gc_registry.account.schemas import AccountRead, AccountUpdate
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import CertificateStatus
from gc_registry.user.models import UserAccountLink
from gc_registry.user.services import get_users_by_account_id


def get_account_by_id(account_id: int, read_session: Session):
    stmt: SelectOfScalar = select(Account).where(Account.id == account_id)
    account = read_session.exec(stmt).first()
    return account


def get_account_summary(account: Account, read_session: Session) -> dict:
    """Get a summary of an account's certificates and devices.

    Args:
        account (Account): The account to get a summary for.
        read_session (Session): The read session.

    Returns:
        dict: A summary of the account.
    """

    num_devices = len(account.devices) if account.devices else 0

    num_devices_by_type = {
        device_type: len(
            [d for d in account.devices if d.technology_type == device_type]
        )
        for device_type in {d.technology_type for d in account.devices}
    }

    device_capacity_by_type = {
        device_type: sum(
            [d.capacity for d in account.devices if d.technology_type == device_type]
        )
        for device_type in {d.technology_type for d in account.devices}
    }

    num_granular_certificate_bundles = read_session.exec(
        select(func.count(GranularCertificateBundle.id)).where(
            GranularCertificateBundle.account_id == account.id
        )
    ).first()

    if not num_granular_certificate_bundles:
        num_granular_certificate_bundles = 0

    num_cancelled_granular_certificate_bundles = read_session.exec(
        select(func.count(GranularCertificateBundle.id)).where(
            GranularCertificateBundle.account_id == account.id,
            GranularCertificateBundle.certificate_bundle_status
            == CertificateStatus.CANCELLED,
        )
    ).first()

    if not num_cancelled_granular_certificate_bundles:
        num_cancelled_granular_certificate_bundles = 0

    total_certificate_energy = read_session.exec(
        select(func.sum(GranularCertificateBundle.bundle_quantity)).where(
            GranularCertificateBundle.account_id == account.id
        )
    ).first()

    if not total_certificate_energy:
        total_certificate_energy = 0

    stmt = (  # type: ignore
        select(  # type: ignore
            GranularCertificateBundle.energy_source,
            func.sum(GranularCertificateBundle.bundle_quantity),
        )
        .where(GranularCertificateBundle.account_id == account.id)
        .group_by(GranularCertificateBundle.energy_source)
    )
    energy_by_fuel_type = {r[0]: r[1] for r in read_session.exec(stmt).all()}

    account_summary = {
        "id": account.id,
        "account_name": account.account_name,
        "num_devices": num_devices,
        "num_devices_by_type": num_devices_by_type,
        "device_capacity_by_type": device_capacity_by_type,
        "num_granular_certificate_bundles": num_granular_certificate_bundles,
        "num_cancelled_granular_certificate_bundles": num_cancelled_granular_certificate_bundles,
        "total_certificate_energy": total_certificate_energy,
        "energy_by_fuel_type": energy_by_fuel_type,
    }

    return account_summary


def get_accounts_by_user_id(
    user_id: int | None, read_session: Session
) -> list[AccountRead] | None:
    """Get accounts by user ID.

    Args:
        user_id (int): The ID of the user.
        read_session (Session): The read session.

    Returns:
        list[AccountRead] | None: List of accounts or None if no accounts are found.
    """
    if not user_id:
        raise ValueError("User ID is required")

    stmt: SelectOfScalar = (
        select(Account)
        .join(UserAccountLink)
        .where(
            UserAccountLink.user_id == user_id,
            UserAccountLink.is_deleted == False,  # noqa: E712
        )
    )
    accounts = read_session.exec(stmt).all()
    if not accounts:
        return None

    account_reads = [AccountRead.model_validate(a.model_dump()) for a in accounts]

    return account_reads


def update_account_user_links(
    account_id: int,
    account_update: AccountUpdate,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
) -> None:
    """Update the user links for an account.

    Args:
        account (Account): The account to update.
        account_update (AccountUpdate): The account update.
        write_session (Session): The write session.
        read_session (Session): The read session.
        esdb_client (EventStoreDBClient): The EventStoreDB client.
    """
    if not account_update.user_ids:
        return

    # Get existing list of users associated with the account
    existing_users = get_users_by_account_id(account_id, read_session)

    if not existing_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="""This account has no users associated with it.
                      Please contact an administrator to add users to this account.""",
        )

    users_to_add = set(account_update.user_ids).difference(
        {user.id for user in existing_users}
    )
    users_to_remove = {
        user.id for user in existing_users if user.id is not None
    }.difference(set(account_update.user_ids))

    for user_id in users_to_add:
        UserAccountLink.create(
            [{"user_id": user_id, "account_id": account_id}],
            write_session,
            read_session,
            esdb_client,
        )

    for user_id in users_to_remove:
        delete_stmt = delete(UserAccountLink).where(
            UserAccountLink.user_id == user_id,
            UserAccountLink.account_id == account_id,
        )
        read_session.exec(delete_stmt)  # type: ignore
        write_session.exec(delete_stmt)  # type: ignore
