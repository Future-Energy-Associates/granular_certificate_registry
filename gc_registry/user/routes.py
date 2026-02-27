import secrets
from typing import Annotated, cast

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from gc_registry.account.models import Account, AccountWhitelistLink
from gc_registry.account.schemas import AccountRead
from gc_registry.account.services import get_accounts_by_user_id
from gc_registry.authentication.services import (
    get_current_active_admin,
    get_current_user,
    get_password_hash,
)
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.logging_config import log_context, logger
from gc_registry.user.models import User, UserAccountLink
from gc_registry.user.schemas import (
    CreateTestAccount,
    CreateTestAccountResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from gc_registry.user.validation import validate_user_role

# Router initialisation
router = APIRouter(tags=["Users"])

LoggedInUser = Annotated[User, Depends(get_current_user)]

### User ###


@router.post("/create", response_model=UserRead)
def create_user(
    user_base: UserCreate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    with log_context(
        operation="create_user",
        admin_user_id=current_user.id,
        new_user_email=user_base.email,
    ):
        validate_user_role(current_user, required_role=UserRoles.ADMIN)
        user_base.hashed_password = get_password_hash(user_base.password)

        existing_user = read_session.exec(
            select(User).where(User.email == user_base.email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_base.email} already exists.",
            )

        user = User.create(user_base, write_session, read_session, esdb_client)

        logger.info("User created successfully", extra={"new_user_id": user[0].id if user else None})

        return user


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: LoggedInUser, read_session: Session = Depends(db.get_read_session)
) -> UserRead:
    user_read = UserRead.model_validate(current_user.model_dump())
    user_accounts = get_accounts_by_user_id(current_user.id, read_session)
    user_read.accounts = user_accounts
    return user_read


@router.get("/me/accounts", response_model=list[AccountRead] | None)
def read_current_user_accounts(
    current_user: LoggedInUser, read_session: Session = Depends(db.get_read_session)
) -> list[AccountRead] | None:
    accounts = get_accounts_by_user_id(current_user.id, read_session)
    return accounts


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    read_session: Session = Depends(db.get_read_session),
):
    validate_user_role(current_user, required_role=UserRoles.AUDIT_USER)
    user = User.by_id(user_id, read_session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )
    user_read = UserRead.model_validate(user.model_dump())
    user_accounts = get_accounts_by_user_id(user_id, read_session)

    user_read.accounts = user_accounts

    return user_read


@router.patch("/update/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Users can update their own information. Admins can update any user information.

    This endpoint cannot be used to change the User role, use /change_role/{user_id} instead.
    """
    with log_context(
        operation="update_user",
        target_user_id=user_id,
        current_user_id=current_user.id,
    ):
        if (current_user.role != UserRoles.ADMIN) and (current_user.id != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to update other users' information.",
            )
        if user_update.role is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="""This endpoint cannot be used to change the User role, use /change_role/{user_id}
                          as an Admin instead.""",
            )
        user = User.by_id(user_id, write_session)

        updated_user = user.update(user_update, write_session, read_session, esdb_client)
        logger.info("User updated successfully")
        return updated_user


@router.delete("/delete/{id}", response_model=UserRead)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    with log_context(
        operation="delete_user",
        target_user_id=user_id,
        admin_user_id=current_user.id,
    ):
        validate_user_role(current_user, required_role=UserRoles.ADMIN)

        user = User.by_id(user_id, read_session)
        deleted_user = user.delete(write_session, read_session, esdb_client)
        logger.info("User deleted successfully")
        return deleted_user


@router.post("/change_role/{user_id}", response_model=UserRead)
def change_role(
    user_id: int,
    role: UserRoles,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    with log_context(
        operation="change_user_role",
        target_user_id=user_id,
        admin_user_id=current_user.id,
        new_role=role.value,
    ):
        validate_user_role(current_user, required_role=UserRoles.ADMIN)

        user = User.by_id(user_id, write_session)
        role_update = UserUpdate(role=role)
        updated_user = user.update(role_update, write_session, read_session, esdb_client)
        logger.info("User role changed successfully")
        return updated_user


@router.post("/create_test_account")
def create_test_account(
    webinar_signup: CreateTestAccount,
    current_user: User = Depends(get_current_active_admin),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
) -> CreateTestAccountResponse:
    """For internal use only.

    Given a user who has signed up post-webinar for a test account, perform the following actions:

    1. Create a new user in the database with the email address of the webinar signup.
    2. Create a new empty account for this user.
    3. Give this user access to the central test account that recieves the daily Elexon issuances.
    4. Whitelist this user's own account to the central test account to allow transfer actions.

    Returns the user and account details, as well as the password to be returned to the user.
    """
    with log_context(
        operation="create_test_account",
        admin_user_id=current_user.id,
        new_user_email=webinar_signup.email,
        organisation=webinar_signup.organisation,
    ):
        existing_user = read_session.exec(
            select(User).where(User.email == webinar_signup.email)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {webinar_signup.email} already exists.",
            )

        # Create a random password for the user
        random_password = secrets.token_urlsafe(12)

        user_base = UserCreate(
            email=webinar_signup.email,
            name=webinar_signup.name,
            organisation=webinar_signup.organisation,
            password=random_password,
            hashed_password=get_password_hash(random_password),
            role=UserRoles.PRODUCTION_USER,
        )

        _user = User.create(user_base, write_session, read_session, esdb_client)
        if not _user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create user please contact support.",
            )
        user: User = cast(User, _user[0])
        user_dict = user.model_dump()

        # Create a new empty account for the user
        account_dict = {
            "account_name": webinar_signup.organisation,
            "user_ids": [user.id],
        }
        _account = Account.create(account_dict, write_session, read_session, esdb_client)
        if _account is not None:
            account: Account = cast(Account, _account[0])

        # Retrieve the central test account
        _central_test_account = read_session.exec(
            select(Account).where(Account.account_name == "Test Account")
        ).first()
        if _central_test_account is not None:
            central_test_account: Account = cast(Account, _central_test_account)

        # Link the user to both their own account and the central test account
        user_account_link_dict_own = {"user_id": user.id, "account_id": account.id}
        user_account_link_dict_central = {
            "user_id": user.id,
            "account_id": central_test_account.id,
        }
        _ = UserAccountLink.create(
            user_account_link_dict_own, write_session, read_session, esdb_client
        )
        _ = UserAccountLink.create(
            user_account_link_dict_central, write_session, read_session, esdb_client
        )

        # Whitelist the user's own account to the central test account
        white_list_link_dict_recieve = {
            "target_account_id": account.id,
            "source_account_id": central_test_account.id,
        }
        white_list_link_dict_send = {
            "target_account_id": central_test_account.id,
            "source_account_id": account.id,
        }
        _ = AccountWhitelistLink.create(
            white_list_link_dict_recieve, write_session, read_session, esdb_client
        )
        _ = AccountWhitelistLink.create(
            white_list_link_dict_send, write_session, read_session, esdb_client
        )

        user_dict.update({"id": user.id, "account_name": account.account_name})

        logger.info(
            "Test account created successfully",
            extra={"new_user_id": user.id, "new_account_id": account.id},
        )

        return CreateTestAccountResponse(
            user=UserRead.model_validate(user_dict),
            account=AccountRead.model_validate(account.model_dump()),
            password=random_password,
        )
