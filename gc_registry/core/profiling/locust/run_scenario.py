from locust import HttpUser, between, task


class BackendUser(HttpUser):
    wait_time = between(5, 10)
    host = "http://localhost:8000"

    @task
    def query_transfer_certificates(self):
        response = self.client.post(
            "/auth/login",
            data={
                "username": "admin_user@usermail.com",
                "password": "admin",
            },
        )

        response.raise_for_status()

        token = response.json()["access_token"]

        payload = {
            "source_id": 1,
            "user_id": 1,
        }
        headers = {"Authorization": f"Bearer {token}"}
        self.client.post("/certificate/query", json=payload, headers=headers)


# class FrontendUser(HttpUser):
#     wait_time = between(1, 5)
#     host = "http://localhost:3000"

#     @task
#     def load_frontend(self):
#         self.client.get("/")
