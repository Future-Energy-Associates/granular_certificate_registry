import datetime
from gc_registry.certificate.event_example.application import Registry


def test_registry():
    # Construct application object.
    registry = Registry()

    # Evolve application state.
    certificate_bundle_data = {
        "device_id": 1,
        "account_id": 1,
        "start_datetime": datetime.datetime(2024, 1, 1, 0, 0, 0),
        "end_datetime": datetime.datetime(2024, 1, 1, 0, 30, 0),
        "certificate_status": "active",
        "face_value": 88,
    }
    gcb_id = registry.issue_certificate(**certificate_bundle_data)
    registry.transfer(gcb_id, account_id=2)
    registry.cancel(gcb_id)

    # Query application state.
    gcb = registry.get_granular_certificate_bundle(gcb_id)
    assert gcb["device_id"] == 1
    assert gcb["face_value"] == 88
    assert gcb["certificate_status"] == "cancelled"

    # Select notifications.
    notifications = registry.notification_log.select(start=1, limit=10)
    assert len(notifications) == 3

    del registry

    registry = Registry()
    gcb = registry.get_granular_certificate_bundle(gcb_id)
    assert gcb["device_id"] == 1
    assert gcb["face_value"] == 88
    assert gcb["certificate_status"] == "cancelled"
