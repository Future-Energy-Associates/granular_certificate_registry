import json

from esdbclient import EventStoreDBClient
from sqlmodel import Session, select

from gc_registry.account.models import Account
from gc_registry.core.database.cqrs import (
    delete_database_entities,
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
        fake_db_account: Account,
        fake_db_user: User,
        esdb_client: EventStoreDBClient,
    ):
        # Write entities to database
        _ = write_to_database(
            entities=[fake_db_wind_device, fake_db_user],
            write_session=db_write_session,
            read_session=db_read_session,
            esdb_client=esdb_client,
        )

        # Check that the events were created in the correct order
        events = esdb_client.get_stream("events", stream_position=0)

        # Init Event plus two CREATE events
        assert len(events) == 3

        event_0_data = json.loads(events[1].data)

        assert events[1].type == "CREATE"
        assert event_0_data["entity_name"] == "Device"
        assert event_0_data["entity_id"] == fake_db_wind_device.id

        event_1_data = json.loads(events[2].data)

        assert events[2].type == "CREATE"
        assert event_1_data["entity_name"] == "User"
        assert event_1_data["entity_id"] == fake_db_user.id

        assert event_0_data["timestamp"] < event_1_data["timestamp"]

        # Check that the read database contains the same as the write database
        wind_device = db_read_session.exec(
            select(Device).filter(Device.id == fake_db_wind_device.id)
        ).first()
        if wind_device is not None:
            assert wind_device == fake_db_wind_device

        user = db_read_session.exec(
            select(User).filter(User.id == fake_db_user.id)
        ).first()
        if user is not None:
            assert user == fake_db_user

    def test_update_entity(
        self,
        db_write_session: Session,
        db_read_session: Session,
        fake_db_wind_device: Device,
        fake_db_account: Account,
        esdb_client: EventStoreDBClient,
    ):
        # Write entities to database first
        _ = write_to_database(
            entities=fake_db_wind_device,
            write_session=db_write_session,
            read_session=db_read_session,
            esdb_client=esdb_client,
        )

        # Update the device with new parameters
        device_update = DeviceUpdate(device_name="new_fake_wind_device")

        # Update the device with new parameters
        update_database_entity(
            entity=fake_db_wind_device,
            update_entity=device_update,
            write_session=db_write_session,
            read_session=db_read_session,
            esdb_client=esdb_client,
        )

        # Check that the event item contains the correct information
        events = esdb_client.get_stream("events", stream_position=0)
        event_data = json.loads(events[-1].data)

        assert events[-1].type == "UPDATE"
        assert event_data["attributes_before"] == {"device_name": "fake_wind_device"}
        assert event_data["attributes_after"] == {"device_name": "new_fake_wind_device"}

        # Check that the read database contains the updated device
        wind_device = db_read_session.exec(
            select(Device).filter(Device.id == fake_db_wind_device.id)
        ).first()
        if wind_device is not None:
            assert wind_device.device_name == "new_fake_wind_device"

    def test_delete_entity(
        self,
        db_write_session: Session,
        db_read_session: Session,
        fake_db_wind_device: Device,
        fake_db_account: Account,
        esdb_client: EventStoreDBClient,
    ):
        # Write entities to database first
        _ = write_to_database(
            entities=fake_db_wind_device,
            write_session=db_write_session,
            read_session=db_read_session,
            esdb_client=esdb_client,
        )

        # Delete the device
        delete_database_entities(
            entities=fake_db_wind_device,
            write_session=db_write_session,
            read_session=db_read_session,
            esdb_client=esdb_client,
        )

        # Check that the event item contains the correct information
        events = esdb_client.get_stream("events", stream_position=0)

        assert events[-1].type == "DELETE"

        # Check that the read database contains the updated device
        wind_device = db_read_session.exec(
            select(Device).filter(Device.id == fake_db_wind_device.id)
        ).first()

        if wind_device is not None:
            assert wind_device.is_deleted is True
