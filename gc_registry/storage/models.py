from sqlmodel import Field

from gc_registry.storage.schemas import (
    StorageActionBase,
    StorageChargeRecordBase,
    StorageDischargeRecordBase,
)


class StorageChargeRecord(StorageChargeRecordBase, table=True):
    scr_allocation_id: int = Field(
        description="The unique ID of the Storage Charge Record that allocated the energy of the Storage Device to this SDR.",
        primary_key=True,
    )
    account_id: int = Field(
        foreign_key="account.id",
        description="Each SCR is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    device_id: int = Field(
        foreign_key="device.id",
        description="The Device ID of the Storage Device that is being charged.",
    )


class StorageDischargeRecord(StorageDischargeRecordBase, table=True):
    sdr_allocation_id: int = Field(
        description="The unique ID of this Storage Discharge Record.",
        primary_key=True,
    )
    account_id: int = Field(
        foreign_key="account.id",
        description="Each SDR is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    device_id: int = Field(
        foreign_key="device.id",
        description="The Device ID of the Storage Device that is being charged.",
    )
    scr_allocation_id: int = Field(
        description="The unique ID of the Storage Charge Record that allocated the energy charged into this Storage Device (adjusted for losses) to this SDR.",
        foreign_key="storagechargerecord.scr_allocation_id",
    )


class StorageAction(StorageActionBase, table=True):
    """A record of a User's request to the registry to query SCRs/SDRs within a specified Account."""

    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )
