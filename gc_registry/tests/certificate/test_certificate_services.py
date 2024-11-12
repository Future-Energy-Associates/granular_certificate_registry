import datetime

import pytest
from esdbclient import EventStoreDBClient
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.certificate.models import (
    GranularCertificateActionBase,
    GranularCertificateBundle,
)
from gc_registry.certificate.services import (
    get_max_certificate_id_by_device_id,
    issue_certificates_in_date_range,
    process_certificate_action,
    query_certificates,
    split_certificate_bundle,
    validate_granular_certificate_bundle,
)
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.models import Device
from gc_registry.settings import settings
from gc_registry.user.models import User


class TestCertificateServices:
    def test_get_max_certificate_id_by_device_id(
        self,
        db_read_session,
        fake_db_wind_device,
        fake_db_solar_device,
        fake_db_gc_bundle,
    ):
        max_certificate_id = get_max_certificate_id_by_device_id(
            db_read_session, fake_db_wind_device.id
        )
        assert max_certificate_id == fake_db_gc_bundle.bundle_id_range_end

    def test_get_max_certificate_id_by_device_id_no_certificates(
        self,
        db_read_session,
        fake_db_wind_device,
    ):
        max_certificate_id = get_max_certificate_id_by_device_id(
            db_read_session, fake_db_wind_device.id
        )
        assert max_certificate_id is None

    def test_validate_granular_certificate_bundle(
        self,
        db_read_session,
        fake_db_wind_device,
        fake_db_solar_device,
        fake_db_gc_bundle,
    ):
        hours = settings.CERTIFICATE_GRANULARITY_HOURS

        gcb_dict = fake_db_gc_bundle.model_dump()

        # Test case 1: certificate already exists for the device in the given period
        # This will fail because the bundle_id_range_start is not equal to the max_certificate_id + 1
        device_max_certificate_id = get_max_certificate_id_by_device_id(
            db_read_session, gcb_dict["device_id"]
        )

        with pytest.raises(ValueError) as exc_info:
            validate_granular_certificate_bundle(
                db_read_session,
                gcb_dict,
                is_storage_device=False,
                device_max_certificate_id=device_max_certificate_id,
            )
        assert "bundle_id_range_start does not match criteria for equal" in str(
            exc_info.value
        )

        # Lets update the bundle_id_range_start to be equal to the max_certificate_id + 1,
        # the bundle_quantity and bundle_id_range_end to be equal to the difference between the bundle ID range
        gcb_dict["bundle_id_range_start"] = fake_db_gc_bundle.bundle_id_range_end + 1
        gcb_dict["bundle_id_range_end"] = (
            gcb_dict["bundle_id_range_start"] + gcb_dict["bundle_quantity"] - 1
        )

        validate_granular_certificate_bundle(
            db_read_session,
            gcb_dict,
            is_storage_device=False,
            device_max_certificate_id=device_max_certificate_id,
        )

        # Test case 2: certificate face value is greater than the device max watts hours
        # This will fail because the bundle_quantity is greater than the device max watts hours

        gcb_dict["bundle_quantity"] = (fake_db_wind_device.capacity * hours) + 1
        gcb_dict["bundle_id_range_end"] = (
            gcb_dict["bundle_id_range_start"] + gcb_dict["bundle_quantity"]
        )

        with pytest.raises(ValueError) as exc_info:
            validate_granular_certificate_bundle(
                db_read_session,
                gcb_dict,
                is_storage_device=False,
                device_max_certificate_id=device_max_certificate_id,
            )
        assert "bundle_quantity does not match criteria for less_than" in str(
            exc_info.value
        )

        gcb_dict["bundle_quantity"] = (fake_db_wind_device.capacity * hours) - 1
        gcb_dict["bundle_id_range_end"] = (
            gcb_dict["bundle_id_range_start"] + gcb_dict["bundle_quantity"] - 1
        )

        validate_granular_certificate_bundle(
            db_read_session,
            gcb_dict,
            is_storage_device=False,
            device_max_certificate_id=device_max_certificate_id,
        )

    def test_issue_certificates_in_date_range(
        self,
        db_write_session,
        db_read_session,
        fake_db_account,
        fake_db_issuance_metadata,
        esdb_client,
    ):
        from_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
        to_datetime = from_datetime + datetime.timedelta(hours=2)
        meter_data_id = "T_RATS-4"

        client = ElexonClient()

        device_capacities = client.get_device_capacities([meter_data_id])

        # create a new device
        device_dict = {
            "device_name": "Ratcliffe on Soar",
            "meter_data_id": meter_data_id,
            "grid": "National Grid",
            "energy_source": "wind",
            "technology_type": "wind",
            "operational_date": str(datetime.datetime(2015, 1, 1, 0, 0, 0)),
            "capacity": device_capacities[meter_data_id],
            "peak_demand": 100,
            "location": "Some Location",
            "account_id": fake_db_account.id,
            "is_storage": False,
        }
        device = Device.create(
            device_dict, db_write_session, db_read_session, esdb_client
        )

        assert device is not None

        issued_certificates = issue_certificates_in_date_range(
            from_datetime,
            to_datetime,
            db_write_session,
            db_read_session,
            esdb_client,
            fake_db_issuance_metadata.id,
            client,
        )

        assert issued_certificates is not None

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

        child_bundle_1, child_bundle_2 = split_certificate_bundle(
            fake_db_gc_bundle, 250, db_write_session, db_read_session, esdb_client
        )

        assert child_bundle_1.bundle_quantity == 250
        assert child_bundle_2.bundle_quantity == 750

        assert (
            child_bundle_1.bundle_id_range_start
            == fake_db_gc_bundle.bundle_id_range_start
        )
        assert (
            child_bundle_1.bundle_id_range_end
            == fake_db_gc_bundle.bundle_id_range_start + 250
        )
        assert (
            child_bundle_2.bundle_id_range_start
            == child_bundle_1.bundle_id_range_end + 1
        )
        assert (
            child_bundle_2.bundle_id_range_end == fake_db_gc_bundle.bundle_id_range_end
        )

    def test_transfer_gcs(
        self,
        fake_db_account: Account,
        fake_db_account_2: Account,
        fake_db_user: User,
        fake_db_gc_bundle: GranularCertificateBundle,
        db_write_session: Session,
        db_read_session: Session,
        esdb_client: EventStoreDBClient,
    ):
        """
        Transfer a fixed number of certificates from one account to another.
        """

        certificate_action = GranularCertificateActionBase(
            action_type="transfer",
            source_id=fake_db_account.id,
            target_id=fake_db_account_2.id,
            user_id=fake_db_user.id,
            source_certificate_issuance_id=fake_db_gc_bundle.issuance_id,
            certificate_quantity=500,
        )

        db_certificate_action = process_certificate_action(
            certificate_action, db_write_session, db_read_session, esdb_client
        )

        assert db_certificate_action.action_response_status == "accepted"  # type: ignore

        # Check that the target account received the split bundle
        certificate_query = GranularCertificateActionBase(
            action_type="query",
            user_id=fake_db_user.id,
            source_id=fake_db_account_2.id,
        )
        certificate_transfered = query_certificates(certificate_query, db_read_session)

        assert certificate_transfered[0].bundle_quantity == 500  # type: ignore
