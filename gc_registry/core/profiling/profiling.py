from typing import Any
from uuid import uuid4

import requests


class RunProfiling:
    def __init__(self):
        self.url = "http://localhost:8000"

    def get_account_by_id(self, account_id):
        url = f"{self.url}/account/{account_id}"
        response = requests.get(url)

        response.raise_for_status()

        return response.json()

    def create_account(self, account_name: str, user_ids: list[int]) -> dict[str, Any]:
        data: dict[str, Any] = {
            "account_name": account_name,
            "user_ids": user_ids,
        }

        response = requests.post(f"{self.url}/account/create", json=data)
        response.raise_for_status()

        return response.json()

    def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        url = f"{self.url}/user/{user_id}"
        response = requests.get(url)

        response.raise_for_status()

        return response.json()

    def get_certificates(
        self, user_id: int, account_id: int, from_date: str, to_date: str
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_id": account_id,
            "user_id": user_id,
            "certificate_period_start": from_date,
            "certificate_period_end": to_date,
        }

        response = requests.post(f"{self.url}/certificate/query", json=data)
        response.raise_for_status()

        return response.json()

    def update_whitelist(
        self, account_id: int, accounts_to_whitelist: list[int]
    ) -> dict[str, Any]:
        data = {"add_to_whitelist": accounts_to_whitelist}
        response = requests.patch(
            f"{self.url}/account/update_whitelist/{account_id}", json=data
        )
        response.raise_for_status()

        return response.json()

    def transfer_certificates(
        self,
        user_id: int,
        source_account_id: int,
        destination_account_id: int,
        certificate_ids: list[int],
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "granular_certificate_bundle_ids": certificate_ids,
            "user_id": user_id,
            "source_id": source_account_id,
            "target_id": destination_account_id,
        }

        response = requests.post(f"{self.url}/certificate/transfer", json=data)
        response.raise_for_status()

        return response.json()

    def run_profiling_sequence(self) -> None:
        account = self.get_account_by_id(1)

        users = account["user_ids"]

        # get the first user
        user = users[0]
        user = self.get_user_by_id(user)

        # get all certificates for the user and account in the last month
        from_date = "2024-01-01"
        to_date = "2024-01-03"
        certificate_bundles = self.get_certificates(
            user["id"], account["id"], from_date, to_date
        )

        # Create new account
        uuid = uuid4()
        new_account = self.create_account(f"Test Account {uuid}", [user["id"]])

        # update whitelist for new account to first account
        account_id = new_account["id"]
        account_whitelist_update = [account["id"]]
        _ = self.update_whitelist(account_id, account_whitelist_update)

        print(certificate_bundles)
        # transfer all certificates from first account to new account
        bundle_ids = [
            bundle["id"]
            for bundle in certificate_bundles["granular_certificate_bundles"]
        ]
        response = self.transfer_certificates(
            user["id"], account["id"], new_account["id"], bundle_ids
        )
        print(response)


if __name__ == "__main__":
    profiling = RunProfiling()

    profiling.run_profiling_sequence()
