from sqlmodel import Session

from gc_registry.device.models import Device


def test_fixtures_work(
    db_session: Session, fake_db_wind_device: Device, fake_db_solar_device: Device
):
    assert 1 == 2


#     assert fake_db_wind_device.device_name == "fake_wind_device"
#     assert fake_db_solar_device.device_name == "fake_solar_device"
