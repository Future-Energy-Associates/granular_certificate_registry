from gc_registry.device.services import get_all_devices, get_device_capacity_by_id


def test_get_device_capacity_by_id(read_session, fake_db_wind_device) -> None:
    device_capacity = get_device_capacity_by_id(read_session, fake_db_wind_device.id)

    assert device_capacity is not None
    assert round(device_capacity, 1) == round(fake_db_wind_device.capacity, 1)


def test_get_all_devices(
    read_session, fake_db_wind_device, fake_db_solar_device
) -> None:
    devices = get_all_devices(read_session)
    assert len(devices) == 2
    assert devices[0].id == fake_db_wind_device.id
    assert devices[1].id == fake_db_solar_device.id
    assert devices[0].capacity == fake_db_wind_device.capacity
    assert devices[1].capacity == fake_db_solar_device.capacity
