from sqlmodel import Session, select

from gc_registry.core.database.cqrs import (
    Event,
    delete_database_entity,
    update_database_entity,
    write_to_database,
)
from gc_registry.device.models import Device, DeviceUpdate
from gc_registry.user.models import User


class TestCQRS:
    def test_create_entity(
        self,
        db_write_session: Session,
        db_read_session: Session,
        fake_db_wind_device: Device,
        fake_db_user: User,
    ):
        # Write entities to database
        write_to_database(
            entities=[fake_db_wind_device, fake_db_user],
            write_session=db_write_session,
            read_session=db_read_session,
        )

        # Check that the events were created in the correct order
        events = db_write_session.exec(select(Event)).all()
        events = [event[0] for event in events]

        assert len(events) == 2

        assert events[0].entity_name == "Device"
        assert events[0].event_type == "CREATE"
        assert events[0].id == 1
        assert events[0].entity_id == fake_db_wind_device.id

        assert events[1].entity_name == "User"
        assert events[1].event_type == "CREATE"
        assert events[1].id == 2
        assert events[1].entity_id == fake_db_user.id

        assert events[0].timestamp < events[1].timestamp

        # Check that the read database contains the same as the write database
        wind_device = db_read_session.exec(
            select(Device).filter(Device.id == fake_db_wind_device.id)
        ).first()
        if wind_device is not None:
            assert wind_device[0] == fake_db_wind_device

        user = db_read_session.exec(
            select(User).filter(User.id == fake_db_user.id)
        ).first()
        if user is not None:
            assert user[0] == fake_db_user

    def test_update_entity(
        self,
        db_write_session: Session,
        db_read_session: Session,
        fake_db_wind_device: Device,
    ):
        # Write entities to database first
        write_to_database(
            entities=fake_db_wind_device,
            write_session=db_write_session,
            read_session=db_read_session,
        )

        # Update the device with new parameters
        device_update = DeviceUpdate(device_name="new_fake_wind_device")

        # Update the device with new parameters
        update_database_entity(
            entity=fake_db_wind_device,
            update_entity=device_update,
            write_session=db_write_session,
            read_session=db_read_session,
        )

        # Check that the event item contains the correct information
        events = db_write_session.exec(select(Event)).all()
        events = [event[0] for event in events]
        event = events[-1]

        assert event.event_type == "UPDATE"
        assert event.attributes_before == {"device_name": "fake_wind_device"}
        assert event.attributes_after == {"device_name": "new_fake_wind_device"}

        # Check that the read database contains the updated device
        wind_device = db_read_session.exec(
            select(Device).filter(Device.id == fake_db_wind_device.id)
        ).first()
        if wind_device is not None:
            assert wind_device[0].device_name == "new_fake_wind_device"

    def test_delete_entity(
        self,
        db_write_session: Session,
        db_read_session: Session,
        fake_db_wind_device: Device,
    ):
        # Write entities to database first
        write_to_database(
            entities=fake_db_wind_device,
            write_session=db_write_session,
            read_session=db_read_session,
        )

        # Delete the device
        delete_database_entity(
            entity=fake_db_wind_device,
            write_session=db_write_session,
            read_session=db_read_session,
        )

        # Check that the event item contains the correct information
        events = db_write_session.exec(select(Event)).all()
        events = [event[0] for event in events]
        event = events[-1]

        assert event.event_type == "DELETE"

        # Check that the read database contains the updated device
        wind_device = db_read_session.exec(
            select(Device).filter(Device.id == fake_db_wind_device.id)
        ).first()

        if wind_device is not None:
            assert wind_device[0].is_deleted is True
