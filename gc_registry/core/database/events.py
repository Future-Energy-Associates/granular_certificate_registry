import json
import uuid
from typing import Generator

from esdbclient import EventStoreDBClient, NewEvent, StreamState
from esdbclient.exceptions import NotFound
from fastapi import Depends

from gc_registry.core.models.base import Event, EventTypes
from gc_registry.settings import settings


def yield_esdb_client() -> Generator[EventStoreDBClient, None, None]:
    with EventStoreDBClient(
        uri=f"esdb://{settings.ESDB_CONNECTION_STRING}:2113?tls=false"
    ) as esdb_client:
        try:
            yield esdb_client
        finally:
            esdb_client.close()


def get_esdb_client() -> EventStoreDBClient:
    return next(yield_esdb_client())


def create_event(
    entity_id: int,
    entity_name: str,
    event_type: EventTypes,
    attributes_before: dict | None = None,
    attributes_after: dict | None = None,
    esdb_client: EventStoreDBClient = Depends(get_esdb_client),
    **kwargs,
):
    """Create a single event and append it to the ESDB events stream."""

    event = Event(
        entity_id=entity_id,
        entity_name=entity_name,
        attributes_before=attributes_before,
        attributes_after=attributes_after,
        parent_entity_id=kwargs.get("parent_entity_id"),
    )

    esdb_event = NewEvent(
        id=uuid.uuid4(),
        type=event_type,
        data=event.model_dump_json().encode(),
    )

    esdb_client.append_to_stream(
        stream_name="events",
        current_version=StreamState.ANY,
        events=[esdb_event],
    )


def batch_create_events(
    entity_ids: list[int],
    entity_names: list[str],
    event_type: EventTypes,
    attributes_before: list[dict | None] | None = None,
    attributes_after: list[dict | None] | None = None,
    esdb_client: EventStoreDBClient = Depends(get_esdb_client),
    **kwargs,
):
    """Create a batch of events and append them to the ESDB events stream.

    This is more efficient that calling create_event multiple times due to
    the overhead of establishing a connection to the ESDB server.
    """

    # Create and delete events do not need before and after attribute dicts
    attributes_before = attributes_before or [None] * len(entity_ids)
    attributes_after = attributes_after or [None] * len(entity_ids)

    events = [
        Event(
            entity_id=entity_id,
            entity_name=entity_name,
            parent_entity_id=kwargs.get("parent_entity_id"),
            attributes_before=attributes_before,
            attributes_after=attributes_after,
        )
        for entity_id, entity_name, attributes_before, attributes_after in zip(
            entity_ids, entity_names, attributes_before, attributes_after
        )
    ]

    esdb_events = [
        NewEvent(
            id=uuid.uuid4(),
            type=event_type,
            data=event.model_dump_json().encode(),
        )
        for event in events
    ]

    esdb_client.append_to_stream(
        stream_name="events",
        current_version=StreamState.ANY,
        events=esdb_events,
    )


def retrieve_all_events_for_entity(
    entity_id: int,
    entity_name: str,
    stream_name: str = "events",
    esdb_client: EventStoreDBClient = Depends(get_esdb_client),
):
    """Retrieve all events for an entity from the ESDB events stream."""
    try:
        event_stream = esdb_client.get_stream(stream_name=stream_name)
    except NotFound:
        raise ValueError(f"Stream {stream_name} not found")

    entity_events = []
    for event in event_stream:
        event_data = json.loads(event.data)
        if (
            event_data["entity_id"] == entity_id
            and event_data["entity_name"] == entity_name
        ):
            event_data["type"] = event.type
            entity_events.append(event_data)

            if event_data.get("parent_entity_id") is not None:
                if event_data["parent_entity_id"].startswith("S-"):
                    parent_entity_id = int(event_data["parent_entity_id"].split("-")[1])
                else:
                    parent_entity_id = int(event_data["parent_entity_id"])
                entity_events.extend(
                    retrieve_all_events_for_entity(
                        entity_id=parent_entity_id,
                        entity_name=entity_name,
                        stream_name=stream_name,
                        esdb_client=esdb_client,
                    )
                )

    return entity_events


def reset_eventstore():
    with EventStoreDBClient(
        uri=f"esdb://{settings.ESDB_CONNECTION_STRING}:2113?tls=false"
    ) as esdb_client:
        esdb_client.delete_stream(stream_name="events", current_version=StreamState.ANY)
