from sqlmodel import Session

from gc_registry.account import services
from gc_registry.account.models import Account
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.device.models import Device
from gc_registry.user import services as users_services
from gc_registry.user.models import User


class TestCertificateServices:
    def test_get_account_summary(
        self,
        read_session: Session,
        fake_db_account: Account,
        fake_db_granular_certificate_bundle: GranularCertificateBundle,
        fake_db_wind_device: Device,
        fake_db_solar_device: Device,
    ):
        account = fake_db_account
        account_summary = services.get_account_summary(account, read_session)

        assert account_summary["id"] == account.id
        assert account_summary["account_name"] == account.account_name
        assert account_summary["num_devices"] == 2
        assert account_summary["num_granular_certificate_bundles"] == 1
        assert account_summary["total_certificate_energy"] == 1000
        assert account_summary["energy_by_fuel_type"] == {"wind": 1000}

    def test_get_users_by_account_id(
        self, read_session: Session, fake_db_account: Account, fake_db_user: User
    ):
        assert fake_db_account is not None
        assert fake_db_account.id is not None

        users = users_services.get_users_by_account_id(fake_db_account.id, read_session)

        assert users is not None

        assert len(users) == 1
