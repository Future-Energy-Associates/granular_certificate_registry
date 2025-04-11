from typing import Annotated

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from gc_registry.account.schemas import AccountRead
from gc_registry.account.services import get_accounts_by_user_id
from gc_registry.authentication.services import get_current_user
from gc_registry.core.database import db, events
from gc_registry.core.models.base import UserRoles
from gc_registry.user.models import User
from gc_registry.user.schemas import UserBase, UserRead, UserUpdate
from gc_registry.user.validation import validate_user_role

# Router initialisation
router = APIRouter(tags=["Users"])

LoggedInUser = Annotated[User, Depends(get_current_user)]

### User ###


@router.post("/create", response_model=UserRead)
def create_user(
    user_base: UserBase,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.ADMIN)
    user = User.create(user_base, write_session, read_session, esdb_client)

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

    return user.update(user_update, write_session, read_session, esdb_client)


@router.delete("/delete/{id}", response_model=UserRead)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.ADMIN)

    user = User.by_id(user_id, read_session)
    return user.delete(write_session, read_session, esdb_client)


@router.post("/change_role/{user_id}", response_model=UserRead)
def change_role(
    user_id: int,
    role: UserRoles,
    current_user: User = Depends(get_current_user),
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    validate_user_role(current_user, required_role=UserRoles.ADMIN)

    user = User.by_id(user_id, write_session)
    role_update = UserUpdate(role=role)
    return user.update(role_update, write_session, read_session, esdb_client)
