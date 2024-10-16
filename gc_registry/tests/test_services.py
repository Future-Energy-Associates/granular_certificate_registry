from esdbclient import EventStoreDBClient
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.services import (
    split_certificate_bundle,
    verifiy_bundle_lineage,
)


class TestServices:
    def test_by_id(
        self,
        db_read_session: Session,
        db_write_session: Session,
        fake_db_account: Account,
    ):
        assert fake_db_account.id is not None

        account_in_db = Account.by_id(fake_db_account.id, db_read_session)

        assert account_in_db is not None
        assert account_in_db.account_name == fake_db_account.account_name

    def test_gc_bundle_split(
        self,
        fake_db_gc_bundle: GranularCertificateBundle,
        db_write_session: Session,
        db_read_session: Session,
        esdb_client: EventStoreDBClient,
    ):
        """
        Split the bundle into two and assert that the bundle quantities align post-split,
        and that the hashes of the child bundles are valid derivatives of the
        parent bundle hash.
        """

        gc_bundle = GranularCertificateBundle.by_id(1, db_write_session)

        child_bundle_1, child_bundle_2 = split_certificate_bundle(
            gc_bundle, 250, db_write_session, db_read_session, esdb_client
        )

        assert child_bundle_1.bundle_quantity == 250
        assert child_bundle_2.bundle_quantity == 750

        assert child_bundle_1.bundle_id_range_start == gc_bundle.bundle_id_range_start
        assert (
            child_bundle_1.bundle_id_range_end == gc_bundle.bundle_id_range_start + 250
        )
        assert (
            child_bundle_2.bundle_id_range_start
            == child_bundle_1.bundle_id_range_end + 1
        )
        assert child_bundle_2.bundle_id_range_end == gc_bundle.bundle_id_range_end

        assert verifiy_bundle_lineage(gc_bundle, child_bundle_1)
        assert verifiy_bundle_lineage(gc_bundle, child_bundle_2)
