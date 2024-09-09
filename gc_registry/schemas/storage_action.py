from typing import Union

from sqlmodel import Field

from gc_registry.models.storage_action import StorageActionBase
from gc_registry.schemas import storage


class StorageActionResponse(StorageActionBase):
    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class StorageAction(StorageActionBase, table=True):
    """A record of a User's request to the registry to query SCRs/SDRs within a specified Account."""

    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class SCRQueryResponse(StorageActionResponse):
    filtered_scrs: Union[list[storage.StorageChargeRecord], None]


class SDRQueryResponse(StorageActionResponse):
    filtered_sdrs: Union[list[storage.StorageDischargeRecord], None]
