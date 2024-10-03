from gc_registry.device.services import get_device_capacity_by_id


def test_get_device_capacity_by_id(db_session, fake_db_wind_device) -> None:

    device_capacity = get_device_capacity_by_id(db_session, fake_db_wind_device.id)
    assert round(device_capacity, 1) == round(3000, 1)
