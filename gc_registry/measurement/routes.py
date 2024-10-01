# Imports
from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends
from sqlmodel import Session

from gc_registry import utils
from gc_registry.authentication import services
from gc_registry.core.database import cqrs, db, events
from gc_registry.measurement import models

# Router initialisation
router = APIRouter(tags=["Measurements"])

### Device Meter Readings ###


@router.post("/create", response_model=models.MeasurementReportRead)
def create_measurement(
    measurement_base: models.MeasurementReportBase,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    measurement = models.MeasurementReport.create(
        measurement_base, write_session, read_session, esdb_client
    )

    return measurement


@router.get("/{measurement_id}", response_model=models.MeasurementReportRead)
def read_measurement(
    measurement_id: int,
    read_session: Session = Depends(db.get_read_session),
):
    measurement = models.MeasurementReport.by_id(measurement_id, read_session)

    return measurement


@router.patch("/update/{measurement_id}", response_model=models.MeasurementReportRead)
def update_measurement(
    measurement_id: int,
    measurement_update: models.MeasurementReportUpdate,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    measurement = models.MeasurementReport.by_id(measurement_id, read_session)

    return measurement.update(
        measurement_update, write_session, read_session, esdb_client
    )


@router.delete("/delete/{id}", response_model=models.MeasurementReportRead)
def delete_measurement(
    measurement_id: int,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    db_measurement = models.MeasurementReport.by_id(measurement_id, write_session)
    return db_measurement.delete(write_session, read_session, esdb_client)
