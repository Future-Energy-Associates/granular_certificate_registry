from fastapi import HTTPException
from sqlmodel import Session

from gc_registry.certificate.models import GranularCertificateAction
from gc_registry.core.models.base import UserRoles
from gc_registry.user.models import User


def validate_user_access(
    granular_certificate_action: GranularCertificateAction, read_session: Session
):
    """
    Validate that the user has access to the source account of the desired action.

    Args:
        granular_certificate_action (GranularCertificateAction): The action to validate

    Raises:
        HTTPException: If the user action is rejected, return a 403 with the reason for rejection.
    """

    # Get the user's info
    user = User.by_id(granular_certificate_action.user_id, read_session)

    user_account_ids = [] if user.account_ids is None else user.account_ids

    # Assert that the user has access to the source account
    if granular_certificate_action.source_id not in user_account_ids:
        msg = "User does not have access to the specified source account"
        raise HTTPException(status_code=403, detail=msg)


def validate_user_role(user: User, required_role: UserRoles):
    """
    Validate that the user has the required role to perform the action.

    Args:
        user (User): The user to validate
        required_role (UserRoles): The role required to perform the action

    Raises:
        HTTPException: If the user action is rejected, return a 403 with the reason for rejection.
    """

    # Assert that the user has the required role
    if user.role < required_role:
        msg = f"User does not have the required role: {required_role}"
        raise HTTPException(status_code=403, detail=msg)
