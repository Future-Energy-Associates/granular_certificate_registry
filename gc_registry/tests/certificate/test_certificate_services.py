from gc_registry.certificate.services import get_max_certificate_id_by_device_id


def test_get_max_certificate_id_by_device_id(
    db_session,
    fake_db_wind_device,
    fake_db_solar_device,
    fake_db_granular_certificate_bundle,
):

    max_certificate_id = get_max_certificate_id_by_device_id(
        db_session, fake_db_wind_device.id
    )
    assert max_certificate_id == fake_db_granular_certificate_bundle.bundle_id_range_end
