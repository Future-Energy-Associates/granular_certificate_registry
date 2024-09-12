def test_fixtures_work(fake_db_wind_device, fake_db_solar_device):
    assert fake_db_wind_device.device_name == "fake_wind_device"
    assert fake_db_solar_device.device_name == "fake_solar_device"
