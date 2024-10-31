import datetime

import pytest

from gc_registry.certificate.models import GranularCertificateBundle
from gc_registry.certificate.schemas import (
    GranularCertificateBundleBase,
    GranularCertificateBundleCreate,
)
from gc_registry.certificate.services import (
    create_bundle_hash,
    get_max_certificate_id_by_device_id,
    issue_certificates_in_date_range,
    validate_granular_certificate_bundle,
)
from gc_registry.device.meter_data.elexon.elexon import ElexonClient
from gc_registry.device.models import Device
from gc_registry.settings import settings


def test_certificate_create(
    fake_db_gc_bundle, db_read_session, db_write_session, esdb_client
):
    bundle_dict = fake_db_gc_bundle.model_dump()
    bundle_dict["id"] = None

    fake_db_gc_bundle_2 = GranularCertificateBundleCreate.model_validate(bundle_dict)

    fake_db_gc_bundle_2.hash = create_bundle_hash(fake_db_gc_bundle_2, nonce="")
    fake_db_gc_bundle_2.issuance_id = f"{fake_db_gc_bundle_2.device_id}-{1234}"

    fake_db_gc_bundle = GranularCertificateBundle.create(
        fake_db_gc_bundle_2, db_write_session, db_read_session, esdb_client
    )
    assert fake_db_gc_bundle[0] is not None
    assert fake_db_gc_bundle[0].id is not None


def test_get_max_certificate_id_by_device_id(
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
    db_read_session,
    fake_db_wind_device,
):
    max_certificate_id = get_max_certificate_id_by_device_id(
        db_read_session, fake_db_wind_device.id
    )
    assert max_certificate_id is None


def test_validate_granular_certificate_bundle(
    db_read_session,
    fake_db_wind_device,
    fake_db_solar_device,
    fake_db_gc_bundle,
):
    hours = settings.CERTIFICATE_GRANULARITY_HOURS

    # Test case 1: certificate already exists for the device in the given period
    # This will fail because the bundle_id_range_start is not equal to the max_certificate_id + 1
    gcb_dict = fake_db_gc_bundle.model_dump()
    fake_db_gc_bundle_base = GranularCertificateBundleBase.model_validate(gcb_dict)
    with pytest.raises(ValueError) as exc_info:
        validate_granular_certificate_bundle(
            db_read_session, fake_db_gc_bundle_base, is_storage_device=False
        )
    assert "bundle_id_range_start does not match criteria for equal" in str(
        exc_info.value
    )

    # Lets update the bundle_id_range_start to be equal to the max_certificate_id + 1,
    # the face_value and bundle_id_range_end to be equal to the difference between the bundle ID range
    fake_db_gc_bundle_base.bundle_id_range_start = (
        fake_db_gc_bundle.bundle_id_range_end + 1
    )
    fake_db_gc_bundle_base.bundle_id_range_end = (
        fake_db_gc_bundle_base.bundle_id_range_start + fake_db_gc_bundle_base.face_value
    )

    validate_granular_certificate_bundle(
        db_read_session, fake_db_gc_bundle_base, is_storage_device=False
    )

    # Test case 2: certificate face value is greater than the device max watts hours
    # This will fail because the face_value is greater than the device max watts hours

    fake_db_gc_bundle_base.face_value = (fake_db_wind_device.capacity * hours) + 1
    fake_db_gc_bundle_base.bundle_id_range_end = (
        fake_db_gc_bundle_base.bundle_id_range_start + fake_db_gc_bundle_base.face_value
    )

    with pytest.raises(ValueError) as exc_info:
        validate_granular_certificate_bundle(
            db_read_session, fake_db_gc_bundle_base, is_storage_device=False
        )
    assert "face_value does not match criteria for less_than" in str(exc_info.value)

    fake_db_gc_bundle_base.face_value = (fake_db_wind_device.capacity * hours) - 1
    fake_db_gc_bundle_base.bundle_id_range_end = (
        fake_db_gc_bundle_base.bundle_id_range_start + fake_db_gc_bundle_base.face_value
    )

    validate_granular_certificate_bundle(
        db_read_session, fake_db_gc_bundle_base, is_storage_device=False
    )


def test_issue_certificates_in_date_range(
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
    device = Device.create(device_dict, db_write_session, db_read_session, esdb_client)

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
