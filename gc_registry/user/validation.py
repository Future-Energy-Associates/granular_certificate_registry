from fastapi import HTTPException, status
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.core.models.base import UserRoles
from gc_registry.user.models import User


def validate_user_access(current_user: User, account_id: int, read_session: Session):
    """
    Validate that the user has access to the source account of the desired action.

    Args:
        current_user (User): The user to validate
        account_id (int): The account ID to validate access to
        read_session (Session): The database session to read from

    Raises:
        HTTPException: If the user action is rejected, return a 401 with the reason for rejection.
    """

    account = Account.by_id(account_id, read_session)

    # Assert that the user has access to the source account
    if current_user.id not in account.user_ids:
        msg = "User does not have access to the specified source account"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)


def validate_user_role(user: User, required_role: UserRoles):
    """
    Validate that the user has the required role to perform the action.

    Args:
        user (User): The user to validate
        required_role (UserRoles): The role required to perform the action

    Raises:
        HTTPException: If the user action is rejected, return a 401 with the reason for rejection.
    """

    # Assert that the user has the required role
    if user.role < required_role:
        msg = f"User does not have the required role: {required_role}"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)


def validate_user_role_for_storage_validator(user: User):
    """
    Validate that the user has the required role to perform the action.
    """
    if user.role != UserRoles.STORAGE_VALIDATOR:
        msg = f"User does not have the required role: {UserRoles.STORAGE_VALIDATOR}"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)
