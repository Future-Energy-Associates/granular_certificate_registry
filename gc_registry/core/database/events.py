import uuid

from esdbclient import EventStoreDBClient, NewEvent, StreamState

from gc_registry.core.models.base import Event, EventTypes
from gc_registry.settings import settings

# Initialise the ESDB client in startup
client = EventStoreDBClient(uri=settings.ESDB_CONNECTION_STRING)


def create_event(
    entity_id: int,
    entity_name: str,
    event_type: EventTypes,
    attributes_before: dict | None = None,
    attributes_after: dict | None = None,
    esdb_client: EventStoreDBClient | None = None,
):
    """Create a single event and append it to the ESDB events stream."""
    if esdb_client is None:
        esdb_client = client

    event = Event(
        entity_id=entity_id,
        entity_name=entity_name,
        attributes_before=attributes_before,
        attributes_after=attributes_after,
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
    esdb_client: EventStoreDBClient | None = None,
):
    """Create a batch of events and append them to the ESDB events stream.

    This is more efficient that calling create_event multiple times due to
    the overhead of establishing a connection to the ESDB server.
    """
    if esdb_client is None:
        esdb_client = client

    # Create and delete events do not need before and after attribute dicts
    attributes_before = attributes_before or [None] * len(entity_ids)
    attributes_after = attributes_after or [None] * len(entity_ids)

    events = [
        Event(
            entity_id=entity_id,
            entity_name=entity_name,
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
