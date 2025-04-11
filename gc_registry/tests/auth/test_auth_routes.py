from fastapi.testclient import TestClient

from gc_registry.user.models import User


class TestAuthRoutes:
    def test_login(self, api_client: TestClient, fake_db_user: User):
        response = api_client.post(
            "/auth/login",
            data={"username": fake_db_user.email, "password": "password"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"] is not None

    def test_login_fail(self, api_client: TestClient, fake_db_user: User):
        response = api_client.post(
            "/auth/login",
            data={"username": fake_db_user.email, "password": "wrong_password"},
        )
        assert response.status_code == 401
        assert response.json() == {
            "detail": f"Password for '{fake_db_user.email}' is incorrect."
        }

        response = api_client.post(
            "/auth/login",
            data={"username": "incorrect@wrong.com", "password": "password"},
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "User 'incorrect@wrong.com' not found."}
