from gc_registry.account.models import Account, AccountBase, AccountUpdate


class TestRoutes:
    def test_get_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be read from the database by ID."""
        fake_db_account_from_db = api_client.get(f"account/{fake_db_account.id}")
        fake_db_account_from_db = Account(**fake_db_account_from_db.json())

        assert (
            fake_db_account_from_db == fake_db_account
        ), f"Expected {fake_db_account} but got {fake_db_account_from_db}"

    def test_create_entity(self, api_client):
        """Test that entities can be created in the database via their FastAPI routes."""

        new_account = AccountBase(account_name="Test Account")

        created_account = api_client.post(
            "account/create", data=new_account.model_dump_json()
        )
        created_account = Account(**created_account.json())

        created_account_from_db = api_client.get(f"account/{created_account.id}")
        created_account_from_db = Account(**created_account_from_db.json())

        assert (
            created_account == new_account
        ), f"Expected {new_account} but got {created_account}"

    def test_update_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be updated in the database via their FastAPI routes."""

        updated_account = AccountUpdate(account_name="Test Account UPDATED")

        updated_account = api_client.patch(
            f"account/update/{fake_db_account.id}",
            data=updated_account.model_dump_json(),
        )
        updated_account = AccountUpdate(**updated_account.json())

        updated_account_from_db = api_client.get(f"account/{updated_account.id}")
        updated_account_from_db = Account(**updated_account_from_db.json())

        assert (
            updated_account_from_db.name == updated_account.name
        ), f"Expected {updated_account} but got {updated_account_from_db}"

    def test_delete_entity(self, api_client, fake_db_account: Account):
        """Test that entities can be deleted in the database via their FastAPI routes."""

        _ = api_client.delete(f"account/delete/{fake_db_account.id}")

        deleted_account = api_client.get(f"account/{fake_db_account.id}")
        deleted_account = Account(**deleted_account.json())

        assert (
            deleted_account.is_deleted
        ), f"Expected {fake_db_account} to be deleted but it was not"
