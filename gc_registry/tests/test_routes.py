from gc_registry.account.models import Account, AccountBase


class TestRoutes:
    def test_get_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be read from the database by ID."""
        fake_db_account_from_db = api_client.get(f"account/{fake_db_account.id}")

        assert (
            fake_db_account_from_db == fake_db_account
        ), f"Expected {fake_db_account} but got {fake_db_account_from_db}"

    def test_create_entity(self, api_client):
        """Test that entities can be created in the database via their FastAPI routes."""

        new_account = AccountBase(account_name="Test Account")

        api_client.post("account/create", data=new_account.model_dump_json())

        created_account = api_client.get(f"account/{new_account.id}")

        assert (
            created_account == new_account
        ), f"Expected {new_account} but got {created_account}"

    def test_update_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be updated in the database via their FastAPI routes."""

        updated_account = AccountBase(account_name="Test Account UPDATED")

        api_client.patch(
            f"account/update/{fake_db_account.id}",
            data=updated_account.model_dump_json(),
        )

        updated_account_from_db = api_client.get(f"account/{fake_db_account.id}")

        assert (
            updated_account == updated_account_from_db
        ), f"Expected {updated_account} but got {updated_account_from_db}"

    def test_delete_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be deleted in the database via their FastAPI routes."""
        api_client.delete(f"account/delete/{fake_db_account.id}")

        deleted_account = api_client.get(f"account/{fake_db_account.id}")

        assert (
            deleted_account.is_deleted
        ), f"Expected {fake_db_account} to be deleted but it was not"
