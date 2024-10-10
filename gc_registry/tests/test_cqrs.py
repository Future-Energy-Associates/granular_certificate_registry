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
        device_dict = {
            "device_name": "fake_wind_device_2",
            "grid": "fake_grid",
            "energy_source": "wind",
            "technology_type": "wind",
            "capacity": 3000,
            "account_id": fake_db_account.id,
            "device_type": "wind",
            "is_renewable": True,
            "fuel_source": "wind",
            "location": "USA",
            "capacity_mw": 100,
            "commissioning_date": "2020-01-01",
            "operational_date": "2020-01-01",
            "peak_demand": 100,
            "is_deleted": False,
            "is_storage": False,
        }

        # device_dict = fake_db_wind_device.model_dump()
        wind_device = Device.model_validate(device_dict)
        # wind_device.device_name = None
        wind_device.device_name = "fake_wind_device 2"

        user_dict = fake_db_user.model_dump()
        user_dict["name"] = "fake_user_2"
        user_dict["id"] = None
        user = User.model_validate(user_dict)

        # Write entities to database
        created_entities = write_to_database(
            entities=[wind_device, user],
            write_session=db_write_session,
            read_session=db_read_session,
            esdb_client=esdb_client,
        )

        # Check that the events were created in the correct order
        events = esdb_client.get_stream("events", stream_position=0)

        # Init Event plus two CREATE events
        assert len(events) == 3

        event_0_data = json.loads(events[1].data)

        assert created_entities is not None

        assert events[1].type == "CREATE"
        assert event_0_data["entity_name"] == "Device"
        assert created_entities[0].id is not None  # type: ignore
        assert event_0_data["entity_id"] == created_entities[0].id  # type: ignore

        event_1_data = json.loads(events[2].data)

        assert events[2].type == "CREATE"
        assert event_1_data["entity_name"] == "User"
        assert event_1_data["entity_id"] == created_entities[1].id  # type: ignore

        assert event_0_data["timestamp"] < event_1_data["timestamp"]

        # Check that the read database contains the same as the write database
        assert fake_db_wind_device.id is not None
        wind_device = db_read_session.exec(
            select(Device).filter(Device.id == fake_db_wind_device.id)  # type: ignore
        ).first()
        if wind_device is not None:
            assert wind_device == fake_db_wind_device

        assert fake_db_user.id is not None
        user = db_read_session.exec(
            select(User).filter(User.id == fake_db_user.id)  # type: ignore
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
        # Get the existing device from the database
        assert fake_db_wind_device.id is not None
        existing_entity = Device.by_id(fake_db_wind_device.id, db_write_session)

        # Update the device with new parameters
        device_update = DeviceUpdate(device_name="new_fake_wind_device")

        # Update the device with new parameters
        update_database_entity(
            entity=existing_entity,
            update_entity=device_update,
            write_session=db_write_session,
            read_session=db_read_session,
            esdb_client=esdb_client,
        )

        # Check that the event item contains the correct information
        events = esdb_client.get_stream("events", stream_position=0)
        event_data = json.loads(events[-1].data)

        assert events[-1].type == "UPDATE"
        assert event_data["attributes_before"]["device_name"] == "fake_wind_device"
        assert event_data["attributes_after"]["device_name"] == "new_fake_wind_device"

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
        # Get the existing device from the database
        assert fake_db_wind_device.id is not None
        existing_entity = Device.by_id(fake_db_wind_device.id, db_write_session)

        # Delete the device
        delete_database_entities(
            entities=existing_entity,
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
