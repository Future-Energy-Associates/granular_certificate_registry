import datetime

from gc_registry.account.models import Account, AccountBase, AccountUpdate


class TestRoutes:
    def test_get_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be read from the database by ID."""
        fake_db_account_from_db = api_client.get(f"account/{fake_db_account.id}")
        fake_db_account_from_db = Account(**fake_db_account_from_db.json())

        different_fields = [
            {
                "from_conftest": {field: fake_db_account.__dict__[field]},
                "from_db": {field: fake_db_account_from_db.__dict__[field]},
            }
            for field in fake_db_account.__dict__
            if fake_db_account.__dict__[field]
            != fake_db_account_from_db.__dict__[field]
            if field != "_sa_instance_state"
        ]

        fake_db_account_from_db.created_at = datetime.datetime.fromisoformat(
            fake_db_account_from_db.created_at
        )

        assert (
            fake_db_account_from_db == fake_db_account
        ), f"Objects did not maych. Different fields: {different_fields}"

    def test_create_entity(self, api_client):
        """Test that entities can be created in the database via their FastAPI routes."""

        new_account = AccountBase(account_name="Test Account", user_ids=[1, 2, 3])

        created_account = api_client.post(
            "account/create", data=new_account.model_dump_json()
        )
        created_account = Account(**created_account.json())

        created_account_from_db = api_client.get(f"account/{created_account.id}")
        created_account_from_db = Account(**created_account_from_db.json())

        assert (
            created_account.account_name == created_account_from_db.account_name
        ), f"Expected {new_account.account_name} but got {created_account.account_name}"

        assert (
            created_account.user_ids == created_account_from_db.user_ids
        ), f"Expected {created_account.user_ids} but got {created_account_from_db.user_ids}"

    def test_update_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be updated in the database via their FastAPI routes."""

        updated_account = AccountUpdate(account_name="Test Account UPDATED")

        updated_account_response = api_client.patch(
            f"account/update/{fake_db_account.id}",
            data=updated_account.model_dump_json(),
        )
        updated_account = AccountUpdate(**updated_account_response.json())

        updated_account_from_db = api_client.get(f"account/{fake_db_account.id}")
        updated_account_from_db = Account(**updated_account_from_db.json())

        assert (
            updated_account_from_db.account_name == updated_account.account_name
        ), f"Expected {updated_account} but got {updated_account_from_db}"

    def test_delete_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be deleted in the database via their FastAPI routes."""

        _ = api_client.delete(f"account/delete/{fake_db_account.id}")

        deleted_account = api_client.get(f"account/{fake_db_account.id}")
        deleted_account = Account(**deleted_account.json())

        assert (
            deleted_account.is_deleted
        ), f"Expected {fake_db_account} to be deleted but it was not"
