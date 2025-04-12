import logging
import time

from locust import HttpUser, between, task
from requests.exceptions import ConnectionError, Timeout


class BackendUser(HttpUser):
    wait_time = between(5, 10)
    host = "http://localhost:8000"

    @task
    def query_transfer_certificates(self):
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Get CSRF token
                response = self.client.get("/csrf-token")
                response.raise_for_status()
                csrf_token = response.json()["csrf_token"]

                # Login
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRF-Token": csrf_token,
                }
                json_data = {"username": "admin_user@usermail.com", "password": "admin"}
                response = self.client.post(
                    "/auth/login", data=json_data, headers=headers
                )
                response.raise_for_status()
                token = response.json()["access_token"]

                # Query certificates
                payload = {
                    "source_id": 1,
                    "user_id": 1,
                }
                headers = {
                    "Authorization": f"Bearer {token}",
                    "X-CSRF-Token": csrf_token,
                }
                response = self.client.post(
                    "/certificate/query", json=payload, headers=headers
                )

                # Check success without raising exception
                if response.status_code == 202:
                    bundle_count = len(response.json()["granular_certificate_bundles"])
                    logging.info(f"Success: {bundle_count} bundles returned")
                    break
                else:
                    logging.warning(
                        f"Attempt {attempt+1}: Status {response.status_code} - {response.text}"
                    )

            except (ConnectionError, Timeout) as e:
                if attempt < max_retries - 1:
                    logging.warning(
                        f"Attempt {attempt+1} failed with connection error: {str(e)}. Retrying in {retry_delay}s"
                    )
                    time.sleep(retry_delay)
                else:
                    logging.error(
                        f"All {max_retries} attempts failed. Last error: {str(e)}"
                    )

            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                break


# class FrontendUser(HttpUser):
#     wait_time = between(1, 5)
#     host = "http://localhost:3000"

#     @task
#     def load_frontend(self):
#         self.client.get("/")
