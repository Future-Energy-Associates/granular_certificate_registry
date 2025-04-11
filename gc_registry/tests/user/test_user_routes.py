from fastapi.testclient import TestClient

from gc_registry.account.models import Account
from gc_registry.account.schemas import AccountRead
from gc_registry.user.models import User


class TestUserRoutes:
    def test_read_current_user(
        self, api_client: TestClient, fake_db_user: User, token: str
    ):
        # Test that the current user is returned
        res = api_client.get("/user/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["name"] == fake_db_user.name

        # Test that the current user is not returned if the token is invalid
        res = api_client.get(
            "/user/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Could not validate credentials"

    def test_read_current_user_accounts(
        self,
        api_client: TestClient,
        fake_db_account: Account,
        fake_db_account_2: Account,
        token: str,
    ):
        res = api_client.get(
            "/user/me/accounts", headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        assert [AccountRead.model_validate(a) for a in res.json()] == [
            AccountRead.model_validate(fake_db_account.model_dump()),
            AccountRead.model_validate(fake_db_account_2.model_dump()),
        ]
