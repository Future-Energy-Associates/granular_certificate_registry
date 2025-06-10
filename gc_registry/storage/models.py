from typing import Self

from sqlmodel import Field, Session, select

from gc_registry.storage.schemas import (
    AllocatedStorageRecordBase,
    StorageActionBase,
    StorageRecordBase,
)


class StorageRecord(StorageRecordBase, table=True):
    id: int | None = Field(
        default=None,
        description="A unique identifier for this Storage Record.",
        primary_key=True,
    )
    is_deleted: bool = Field(default=False)

    @classmethod
    def validator_ids_by_device_id(
        cls, device_id: int, read_session: Session
    ) -> list[int]:
        """Retrieve all validator IDs for the specified device."""
        return read_session.exec(
            select(cls.validator_id).where(cls.device_id == device_id)
        ).all()

    @classmethod
    def by_validator_ids(
        cls, validator_ids: list[int], read_session: Session
    ) -> list[Self]:
        """Retrieve all Storage Records with the specified validator IDs."""
        return read_session.exec(
            select(cls).where(cls.validator_id.in_(validator_ids))  # type: ignore
        ).all()


class AllocatedStorageRecord(AllocatedStorageRecordBase, table=True):
    id: int | None = Field(
        default=None,
        description="A unique identifier for this Allocated Storage Record.",
        primary_key=True,
    )
    is_deleted: bool = Field(default=False)


class StorageAction(StorageActionBase, table=True):
    """A record of a User's request to the registry to query SCRs/SDRs within a specified Account."""

    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )
