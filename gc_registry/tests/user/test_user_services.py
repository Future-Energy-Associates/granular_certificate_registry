import pytest
from pydantic import ValidationError
from sqlmodel import Session

from gc_registry.core.models.base import UserRoles
from gc_registry.user.schemas import UserBase


class TestUserServices:
    def test_create_user_with_invalid_email(
        self, write_session: Session, read_session: Session
    ):
        # Correct email format
        _user = UserBase.model_validate(
            {"email": "test@fea.com", "name": "test", "role": UserRoles.ADMIN}
        )

        # Incorrect email format 1
        with pytest.raises(ValidationError):
            _user_incorrect = UserBase.model_validate(
                {"email": "@fea.com", "name": "test", "role": UserRoles.ADMIN}
            )

        # Incorrect email format 2
        with pytest.raises(ValidationError):
            _user_incorrect_2 = UserBase.model_validate(
                {"email": "test@", "name": "test", "role": UserRoles.ADMIN}
            )

        # Incorrect email format 3
        with pytest.raises(ValidationError):
            _user_incorrect_3 = UserBase.model_validate(
                {"email": "test@fea", "name": "test", "role": UserRoles.ADMIN}
            )
