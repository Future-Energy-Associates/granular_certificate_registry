import datetime
from typing import Any, Hashable

import pandas as pd
import pytest
from esdbclient import EventStoreDBClient
from fastapi import HTTPException
from sqlmodel import Session

from gc_registry.account.models import Account
from gc_registry.account.schemas import AccountUpdate
from gc_registry.certificate.models import (
    GranularCertificateBundle,
    IssuanceMetaData,
)
from gc_registry.certificate.schemas import (
    GranularCertificateCancel,
    GranularCertificateQuery,
    GranularCertificateTransfer,
)
from gc_registry.certificate.services import (
    create_issuance_id,
    get_max_certificate_id_by_device_id,
    get_max_certificate_timestamp_by_device_id,
    issue_certificates_by_device_in_date_range,
    issue_certificates_in_date_range,
    process_certificate_bundle_action,
    query_certificate_bundles,
    split_certificate_bundle,
    validate_granular_certificate_bundle,
)
from gc_registry.core.models.base import CertificateStatus
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.meter_data.manual_submission import ManualSubmissionMeterClient
from gc_registry.device.models import Device
from gc_registry.measurement.models import MeasurementReport
from gc_registry.measurement.services import (
    parse_measurement_json,
    serialise_measurement_csv,
)
from gc_registry.settings import settings
from gc_registry.user.models import User


class TestCertificateServices:
    def test_get_max_certificate_id_by_device_id(
        self,
        db_read_session,
        fake_db_wind_device,
        fake_db_granular_certificate_bundle,
    ):
        max_certificate_id = get_max_certificate_id_by_device_id(
            db_read_session, fake_db_wind_device.id
        )
        assert (
            max_certificate_id
            == fake_db_granular_certificate_bundle.bundle_id_range_end
        )

    def test_get_max_certificate_id_by_device_id_no_certificates(
        self,
        db_read_session,
        fake_db_wind_device,
    ):
        max_certificate_id = get_max_certificate_id_by_device_id(
            db_read_session, fake_db_wind_device.id
        )
        assert max_certificate_id is None

    def test_get_max_certificate_timestamp_by_device_id(
        self,
        db_read_session,
        fake_db_wind_device,
        fake_db_granular_certificate_bundle,
    ):
        max_certificate_timestamp = get_max_certificate_timestamp_by_device_id(
            db_read_session, fake_db_wind_device.id
        )
        assert (
            max_certificate_timestamp
            == fake_db_granular_certificate_bundle.production_ending_interval
        )
        assert isinstance(max_certificate_timestamp, datetime.datetime)

    def test_validate_granular_certificate_bundle(
        self,
        db_read_session,
        fake_db_wind_device,
        fake_db_granular_certificate_bundle,
    ):
        hours = settings.CERTIFICATE_GRANULARITY_HOURS

        gcb_dict = fake_db_granular_certificate_bundle.model_dump()

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
                max_certificate_id=device_max_certificate_id,
            )
        assert "bundle_id_range_start does not match criteria for equal" in str(
            exc_info.value
        )

        # Lets update the bundle_id_range_start to be equal to the max_certificate_id + 1,
        # the bundle_quantity and bundle_id_range_end to be equal to the difference between the bundle ID range
        gcb_dict["bundle_id_range_start"] = (
            fake_db_granular_certificate_bundle.bundle_id_range_end + 1
        )
        gcb_dict["bundle_id_range_end"] = (
            gcb_dict["bundle_id_range_start"] + gcb_dict["bundle_quantity"] - 1
        )

        validate_granular_certificate_bundle(
            db_read_session,
            gcb_dict,
            is_storage_device=False,
            max_certificate_id=device_max_certificate_id,
        )

        # Test case 2: certificate quantity is greater than the device max watts hours
        # This will fail because the bundle_quantity is greater than the device max watts hours

        gcb_dict["bundle_quantity"] = (fake_db_wind_device.capacity * hours) * 1.5
        gcb_dict["bundle_id_range_end"] = (
            gcb_dict["bundle_id_range_start"] + gcb_dict["bundle_quantity"]
        )

        with pytest.raises(ValueError) as exc_info:
            validate_granular_certificate_bundle(
                db_read_session,
                gcb_dict,
                is_storage_device=False,
                max_certificate_id=device_max_certificate_id,
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
            max_certificate_id=device_max_certificate_id,
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

    def test_split_certificate_bundle(
        self,
        fake_db_granular_certificate_bundle: GranularCertificateBundle,
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
            fake_db_granular_certificate_bundle,
            250,
            db_write_session,
            db_read_session,
            esdb_client,
        )

        assert child_bundle_1.bundle_quantity == 250
        assert child_bundle_2.bundle_quantity == 750

        assert (
            child_bundle_1.bundle_id_range_start
            == fake_db_granular_certificate_bundle.bundle_id_range_start
        )
        assert (
            child_bundle_1.bundle_id_range_end
            == fake_db_granular_certificate_bundle.bundle_id_range_start + 250
        )
        assert (
            child_bundle_2.bundle_id_range_start
            == child_bundle_1.bundle_id_range_end + 1
        )
        assert (
            child_bundle_2.bundle_id_range_end
            == fake_db_granular_certificate_bundle.bundle_id_range_end
        )

    def test_transfer_gcs(
        self,
        fake_db_account: Account,
        fake_db_account_2: Account,
        fake_db_user: User,
        fake_db_granular_certificate_bundle: GranularCertificateBundle,
        db_write_session: Session,
        db_read_session: Session,
        esdb_client: EventStoreDBClient,
    ):
        """
        Transfer a fixed number of certificates from one account to another.
        """

        assert fake_db_account.id is not None
        assert fake_db_account_2.id is not None
        assert fake_db_user.id is not None
        assert fake_db_granular_certificate_bundle.id is not None

        # Whitelist the source account for the target account
        fake_db_account_2 = db_write_session.merge(fake_db_account_2)
        fake_db_account_2.update(
            AccountUpdate(account_whitelist=[fake_db_account.id]),  # type: ignore
            db_write_session,
            db_read_session,
            esdb_client,
        )

        certificate_transfer = GranularCertificateTransfer(
            source_id=fake_db_account.id,  # type: ignore
            target_id=fake_db_account_2.id,  # type: ignore
            user_id=fake_db_user.id,
            granular_certificate_bundle_ids=[fake_db_granular_certificate_bundle.id],
            certificate_quantity=500,
        )

        assert hasattr(
            certificate_transfer, "action_type"
        ), f"Action type not set: {certificate_transfer}"

        _ = process_certificate_bundle_action(
            certificate_transfer, db_write_session, db_read_session, esdb_client
        )

        # Check that the target account received the split bundle
        certificate_query = GranularCertificateQuery(
            user_id=fake_db_user.id,
            source_id=fake_db_account_2.id,  # type: ignore
        )
        certificate_transfered = query_certificate_bundles(
            certificate_query, db_read_session
        )

        assert certificate_transfered is not None
        assert certificate_transfered[0].bundle_quantity == 500

        # De-whitelist the account and verfiy the transfer is rejected
        fake_db_account_2.update(
            AccountUpdate(account_whitelist=[]),  # type: ignore
            db_write_session,
            db_read_session,
            esdb_client,
        )

        certificate_transfer = GranularCertificateTransfer(
            source_id=fake_db_account.id,  # type: ignore
            target_id=fake_db_account_2.id,  # type: ignore
            user_id=fake_db_user.id,
            granular_certificate_bundle_ids=[fake_db_granular_certificate_bundle.id],
            certificate_quantity=500,
        )

        with pytest.raises(HTTPException):
            _db_certificate_action = process_certificate_bundle_action(
                certificate_transfer, db_write_session, db_read_session, esdb_client
            )

    def test_cancel_by_percentage(
        self,
        fake_db_granular_certificate_bundle: GranularCertificateBundle,
        fake_db_user: User,
        db_write_session: Session,
        db_read_session: Session,
        esdb_client: EventStoreDBClient,
    ):
        """
        Cancel 75% of the bundle, and assert that the bundle was correctly
        split and the correct percentage cancelled.
        """

        # check that all the test fixtures have ids
        assert fake_db_granular_certificate_bundle.id is not None
        assert fake_db_user.id is not None

        certificate_action = GranularCertificateCancel(
            source_id=fake_db_granular_certificate_bundle.account_id,
            user_id=fake_db_user.id,
            granular_certificate_bundle_ids=[fake_db_granular_certificate_bundle.id],
            certificate_bundle_percentage=0.75,
        )

        _ = process_certificate_bundle_action(
            certificate_action, db_write_session, db_read_session, esdb_client
        )

        # Check that 75% of the bundle was cancelled
        certificate_query = GranularCertificateQuery(
            user_id=fake_db_user.id,
            source_id=fake_db_granular_certificate_bundle.account_id,
            certificate_status=CertificateStatus.CANCELLED,
        )
        certificates_cancelled = query_certificate_bundles(
            certificate_query, db_read_session
        )

        assert certificates_cancelled[0].bundle_quantity == 750  # type: ignore

    def test_sparse_filter_query(
        self,
        fake_db_granular_certificate_bundle: GranularCertificateBundle,
        fake_db_granular_certificate_bundle_2: GranularCertificateBundle,
        db_read_session: Session,
    ):
        """Test that the query_certificate_bundles function can handle sparse filter input on device ID
        and production starting datetime."""

        issuance_ids = [
            create_issuance_id(fake_db_granular_certificate_bundle),
            create_issuance_id(fake_db_granular_certificate_bundle_2),
        ]

        certificate_query = GranularCertificateQuery(
            user_id=1,
            source_id=fake_db_granular_certificate_bundle.account_id,
            issuance_ids=issuance_ids,
        )

        certificates_from_query = query_certificate_bundles(
            certificate_query, db_read_session
        )

        assert certificates_from_query is not None
        assert len(certificates_from_query) == 2
        assert (
            certificates_from_query[0].device_id
            == fake_db_granular_certificate_bundle.device_id
        )
        assert (
            certificates_from_query[1].device_id
            == fake_db_granular_certificate_bundle_2.device_id
        )
        assert (
            certificates_from_query[0].production_starting_interval
            == fake_db_granular_certificate_bundle.production_starting_interval
        )
        assert (
            certificates_from_query[1].production_starting_interval
            == fake_db_granular_certificate_bundle_2.production_starting_interval
        )

        # Test with an issuance ID that doesn't exist

        certificate_query = GranularCertificateQuery(
            user_id=1,
            source_id=fake_db_granular_certificate_bundle.account_id,
            issuance_ids=["invalid_id"],
        )

        certificates_from_query = query_certificate_bundles(
            certificate_query, db_read_session
        )

    def test_issue_certificates_from_manual_submission(
        self,
        db_write_session: Session,
        db_read_session: Session,
        fake_db_wind_device: Device,
        fake_db_issuance_metadata: IssuanceMetaData,
        esdb_client: EventStoreDBClient,
    ):
        measurement_json = serialise_measurement_csv(
            "gc_registry/tests/data/test_measurements.csv"
        )

        measurement_df: pd.DataFrame = parse_measurement_json(
            measurement_json, to_df=True
        )

        # The device ID may change during testing so we need to update the measurement data
        measurement_df["device_id"] = fake_db_wind_device.id

        readings = MeasurementReport.create(
            measurement_df.to_dict(orient="records"),
            db_write_session,
            db_read_session,
            esdb_client,
        )

        assert readings is not None, "No readings found in the database."
        assert (
            len(readings) == 24 * 31
        ), f"Incorrect number of readings found ({len(readings)}); expected {24 * 31}."

        from_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
        to_datetime = from_datetime + datetime.timedelta(days=31)

        client = ManualSubmissionMeterClient()

        issued_certificates = issue_certificates_by_device_in_date_range(
            fake_db_wind_device,
            from_datetime,
            to_datetime,
            db_write_session,
            db_read_session,
            esdb_client,
            fake_db_issuance_metadata.id,
            client,
        )

        assert issued_certificates is not None
        assert (
            len(issued_certificates) == 24 * 31
        ), f"Incorrect number of certificates issued ({len(issued_certificates)}); expected {24 * 31}."
        assert (
            sum([cert.bundle_quantity for cert in issued_certificates])  # type: ignore
            == measurement_df["interval_usage"].sum()
        ), "Incorrect total certificate quantity issued."

    def test_issue_certificates_from_elexon(
        self,
        db_write_session: Session,
        db_read_session: Session,
        fake_db_account: Account,
        fake_db_wind_device: Device,
        fake_db_issuance_metadata: IssuanceMetaData,
        esdb_client: EventStoreDBClient,
    ):
        from_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
        to_datetime = from_datetime + datetime.timedelta(hours=4)
        meter_data_ids = [
            "E_MARK-1",
            "T_RATS-1",
            "T_RATS-2",
            "T_RATS-3",
            "T_RATS-4",
            "T_RATSGT-2",
            "T_RATSGT-4",
        ]
        meter_data_id = meter_data_ids[0]

        client = ElexonClient()

        device_capacities = client.get_device_capacities([meter_data_id])

        W_IN_MW = 1e6

        # create a new device
        device_dict: dict[Hashable, Any] = {
            "device_name": "Ratcliffe on Soar",
            "meter_data_id": meter_data_id,
            "grid": "National Grid",
            "energy_source": "wind",
            "technology_type": "wind",
            "operational_date": str(datetime.datetime(2015, 1, 1, 0, 0, 0)),
            "capacity": device_capacities[meter_data_id] * W_IN_MW,
            "peak_demand": 100,
            "location": "Some Location",
            "account_id": fake_db_account.id,
            "is_storage": False,
        }
        devices = Device.create(
            device_dict, db_write_session, db_read_session, esdb_client
        )

        if isinstance(devices, list):
            device = devices[0]

        assert devices is not None

        issued_certificates = issue_certificates_by_device_in_date_range(
            device,  # type: ignore
            from_datetime,
            to_datetime,
            db_write_session,
            db_read_session,
            esdb_client,
            fake_db_issuance_metadata.id,
            client,  # type: ignore
        )

        assert issued_certificates is not None
        assert len(issued_certificates) == 5
