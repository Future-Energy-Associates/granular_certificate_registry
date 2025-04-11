import pytest
from sqlmodel import Session

from gc_registry.authentication.services import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    get_user,
    verify_password,
)
from gc_registry.user.models import User


class TestAuthServices:
    def test_verify_password(self):
        assert verify_password("password", get_password_hash("password"))

    def test_get_user(self, read_session: Session, fake_db_user: User):
        user = get_user(fake_db_user.email, read_session)
        assert user is not None
        assert user.name == fake_db_user.name

    def test_authenticate_user(self, read_session: Session, fake_db_user: User):
        user = authenticate_user(fake_db_user.email, "password", read_session)
        assert user.name == fake_db_user.name

    @pytest.mark.asyncio
    async def test_access_token(self, read_session: Session, fake_db_user: User):
        access_token = create_access_token(data={"sub": fake_db_user.email})

        current_user = await get_current_user(access_token, read_session)

        assert current_user.name == fake_db_user.name, "User not found from token"
