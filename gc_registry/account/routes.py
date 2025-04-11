from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

import gc_registry.device.services as device_services
import gc_registry.user.services as user_services
from gc_registry.account.models import (
    Account,
    AccountWhitelistLink,
)
from gc_registry.account.schemas import (
    AccountBase,
    AccountRead,
    AccountSummary,
    AccountUpdate,
    AccountWhitelist,
)
from gc_registry.account.validation import (
    validate_account,
    validate_and_apply_account_whitelist_update,
)
from gc_registry.authentication.services import get_current_user
from gc_registry.certificate.schemas import (
    GranularCertificateBundleRead,
    GranularCertificateQueryRead,
)
from gc_registry.certificate.services import get_certificate_bundles_by_account_id
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.device.models import DeviceRead
from gc_registry.logging_config import logger
from gc_registry.user.models import User, UserAccountLink
from gc_registry.user.validation import validate_user_access, validate_user_role

from . import services

# Router initialisation
router = APIRouter(tags=["Accounts"])


@router.post("/create", status_code=201, response_model=AccountRead)
def create_account(
    account_base: AccountBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.PRODUCTION_USER)
    validate_account(account_base, read_session)

    # By default, create the account as linked to the current user
    account_base.user_ids = account_base.user_ids + [current_user.id]

    accounts = Account.create(account_base, write_session, read_session, esdb_client)
    if not accounts:
        raise HTTPException(status_code=500, detail="Could not create Account")

    account = AccountRead.model_validate(accounts[0].model_dump())

    # Update link table to link the current user and list of associated users to the account
    _user_account_link = UserAccountLink.create(
        [
            {"user_id": user_id, "account_id": account.id}
            for user_id in account_base.user_ids
        ],
        write_session,
        read_session,
        esdb_client,
    )

    return account


@router.get("/{account_id}", response_model=AccountRead)
def read_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    account = Account.by_id(account_id, read_session)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/update/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    account_update: AccountUpdate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, account_id, read_session)

    account = Account.by_id(account_id, write_session)
    if not account or not account.id:
        raise HTTPException(
            status_code=404, detail=f"Account ID not found: {account_id}"
        )

    if account.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot update deleted accounts.")

    if account_update.user_ids is not None:
        services.update_account_user_links(
            account.id, account_update, write_session, read_session, esdb_client
        )

    updated_account = account.update(
        account_update, write_session, read_session, esdb_client
    )

    if not updated_account:
        raise HTTPException(
            status_code=400, detail=f"Error during account update: {account_id}"
        )

    return updated_account


@router.patch("/update_whitelist/{account_id}", response_model=AccountRead)
def update_whitelist(
    account_id: int,
    account_whitelist_update: AccountWhitelist,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, account_id, read_session)

    account = Account.by_id(account_id, read_session)
    if not account:
        raise HTTPException(
            status_code=404, detail=f"Account ID not found: {account_id}"
        )

    validate_and_apply_account_whitelist_update(
        account, account_whitelist_update, write_session, read_session, esdb_client
    )

    return account


@router.get("/{account_id}/whitelist", response_model=list[Account])
def get_whitelist(
    account_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
) -> list[Account] | None:
    """Return the list of accounts that the given account has whitelisted to receive certificates from."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, account_id, read_session)
    account_whitelist = read_session.exec(
        select(AccountWhitelistLink.source_account_id).where(
            AccountWhitelistLink.target_account_id == account_id,
            AccountWhitelistLink.is_deleted == False,  # noqa: E712
        )
    ).all()
    return [
        Account.by_id(id_=account_id, session=read_session)
        for account_id in account_whitelist
    ]


@router.get("/{account_id}/whitelist_inverse", response_model=list[Account])
def get_whitelist_inverse(
    account_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
) -> list[Account] | None:
    """Return the list of accounts that have whitelisted the given account to receive certificates from."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, account_id, read_session)
    account_whitelist_inverse = read_session.exec(
        select(AccountWhitelistLink.target_account_id).where(
            AccountWhitelistLink.source_account_id == account_id,
            AccountWhitelistLink.is_deleted == False,  # noqa: E712
        )
    ).all()
    return [
        Account.by_id(id_=account_id, session=read_session)
        for account_id in account_whitelist_inverse
    ]


@router.delete("/delete/{account_id}", status_code=200, response_model=AccountRead)
def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, account_id, read_session)
    try:
        account = Account.by_id(account_id, write_session)
        accounts = account.delete(write_session, read_session, esdb_client)
        if not accounts:
            raise ValueError(f"Account id {account_id} not found")
        return accounts[0]
    except Exception:
        raise HTTPException(
            status_code=404, detail="Could not delete Account not found"
        )


@router.get("/list", response_model=list[AccountRead])
def list_all_accounts(
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """List all active accounts on the registry."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    accounts = Account.all(read_session)
    return accounts


@router.get("/{account_id}/users", response_model=list[User])
def get_users_by_account_id(
    account_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Get all users associated with an account."""
    validate_user_role(current_user, required_role=UserRoles.ADMIN)
    account = Account.by_id(account_id, read_session)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.is_deleted:
        raise HTTPException(
            status_code=400, detail="Cannot get users for deleted accounts."
        )

    users = user_services.get_users_by_account_id(account_id, read_session)

    if not users:
        raise HTTPException(status_code=404, detail="No users found for account")

    print(users)

    return [user.model_dump() for user in users]


@router.get("/{account_id}/summary", response_model=AccountSummary)
def get_account_summary(
    account_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Get a summary of an account."""
    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)
    account = Account.by_id(account_id, read_session)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if account.is_deleted:
        raise HTTPException(
            status_code=400, detail="Cannot get summary for deleted accounts."
        )

    if not account.id:
        raise HTTPException(status_code=404, detail="Account not found")

    account_summary = services.get_account_summary(account, read_session)

    return AccountSummary.model_validate(account_summary)


@router.get("/{account_id}/devices", response_model=list[DeviceRead])
def get_all_devices_by_account_id(
    account_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)

    # check the account exists
    account = Account.by_id(account_id, read_session)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    devices = device_services.get_devices_by_account_id(account_id, read_session)

    if not devices:
        logger.info(f"No devices found for account {account_id}")
        return []

    for device in devices:
        validate_user_access(current_user, device.account_id, read_session)

    return [device.model_dump() for device in devices]


@router.get("/{account_id}/certificates/devices", response_model=list[DeviceRead])
def get_devices_for_account_certificates(
    account_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Return all devices associated with an account that have certificates issued against them."""
    validate_user_role(current_user, required_role=UserRoles.TRADING_USER)
    validate_user_access(current_user, account_id, read_session)

    devices = device_services.get_certificate_devices_by_account_id(
        read_session, account_id
    )

    if not devices:
        logger.info(f"No devices found for account {account_id} certificates")
        return []

    return [device.model_dump() for device in devices]


@router.get("/{account_id}/certificates", response_model=GranularCertificateQueryRead)
def list_all_account_bundles(
    account_id: int,
    limit: int | None = None,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    """Return all certificate bundles from the specified Account.

    Args:
        account_id (int): The account ID to list certificate bundles from
        limit (int | None): The maximum number of certificate bundles to return

    Returns:
        GranularCertificateQueryRead: The certificate query response
    """

    if not current_user or not current_user.id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)
    validate_user_access(current_user, account_id, read_session)

    certificate_bundles = get_certificate_bundles_by_account_id(
        account_id, read_session, limit
    )

    if not certificate_bundles:
        raise HTTPException(
            status_code=422, detail="No certificates found for this account"
        )

    certificate_bundles_read = [
        GranularCertificateBundleRead.model_validate(certificate.model_dump())
        for certificate in certificate_bundles
    ]

    certificate_query = GranularCertificateQueryRead(
        granular_certificate_bundles=list(certificate_bundles_read),
        source_id=account_id,
        user_id=current_user.id,
    )

    return certificate_query.model_dump()
