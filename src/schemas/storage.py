import uuid as uuid_pkg

from sqlmodel import Field

from src.models.storage import StorageChargeRecordBase, StorageDischargeRecordBase


class StorageChargeRecord(StorageChargeRecordBase, table=True):
    scr_allocation_id: uuid_pkg.UUID = Field(
        description="The unique ID of the Storage Charge Record that allocated the energy of the Storage Device to this SDR.",
        primary_key=True,
    )
    account_id: uuid_pkg.UUID = Field(
        foreign_key="account.account_id",
        description="Each SCR is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    device_id: uuid_pkg.UUID = Field(
        foreign_key="device.device_id",
        description="The Device ID of the Storage Device that is being charged.",
    )


class StorageDischargeRecord(StorageDischargeRecordBase, table=True):
    sdr_allocation_id: uuid_pkg.UUID = Field(
        description="The unique ID of this Storage Discharge Record.",
        primary_key=True,
    )
    device_id: uuid_pkg.UUID = Field(
        foreign_key="device.device_id",
        description="The Device ID of the Storage Device that is being charged.",
    )
    account_id: uuid_pkg.UUID = Field(
        foreign_key="account.account_id",
        description="Each SDR is issued to a single unique production Account that its Storage Device is individually registered to.",
    )
    scr_allocation_id: uuid_pkg.UUID = Field(
        description="The unique ID of the Storage Charge Record that allocated the energy charged into this Storage Device (adjusted for losses) to this SDR.",
        foreign_key="storagechargerecord.scr_allocation_id",
    )
