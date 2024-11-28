import datetime
from functools import partial

from pydantic import BaseModel
from sqlmodel import Field

from gc_registry import utils
from gc_registry.certificate.schemas import (
    GranularCertificateActionBase,
    GranularCertificateBundleBase,
    IssuanceMetaDataBase,
)
from gc_registry.core.models.base import CertificateActionType, CertificateStatus

# issuance_id a unique non-sequential ID related to the issuance of the entire bundle,
# specified as a concatenation of deviceID-EnergyCarrier-ProductionStartDatetime.
# The range of GC IDs within the bundle are unique sequential integers
# that allow the bundle to be split into the underlying GCs. Future splits of the
# bundle will retain the original bundle issuance ID.


class GranularCertificateBundle(
    GranularCertificateBundleBase, utils.ActiveRecord, table=True
):
    id: int | None = Field(
        default=None,
        primary_key=True,
        description="A unique, incremental integer ID assigned to this bundle.",
    )


class GranularCertificateBundleUpdate(BaseModel):
    account_id: int | None = None
    certificate_status: CertificateStatus | None = None
    metadata_id: int | None = None
    bundle_id_range_start: int | None = None
    bundle_id_range_end: int | None = None
    bundle_quantity: int | None = None
    beneficiary: str | None = None


# A Transfer object is specified by a User, and is stored in a transaction table that
# lists all transfers and cancellations between accounts for audit purposes

# "transfer", "recurring_transfer", "cancel", "claim", "withdraw"
utc_datetime_now = partial(datetime.datetime.now, datetime.timezone.utc)


class GranularCertificateAction(
    utils.ActiveRecord, GranularCertificateActionBase, table=True
):
    id: int | None = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )
    action_type: CertificateActionType
    action_request_datetime: datetime.datetime = Field(
        default_factory=utc_datetime_now,
        description="The UTC datetime at which the User submitted the action to the registry.",
    )
    action_completed_datetime: datetime.datetime = Field(
        default_factory=utc_datetime_now,
        description="The UTC datetime at which the registry confirmed to the User that their submitted action had either been successfully completed or rejected.",
    )
    certificate_status: CertificateStatus | None = Field(
        default=None, description="""Filter on the status of the GC Bundles."""
    )


class IssuanceMetaData(IssuanceMetaDataBase, utils.ActiveRecord, table=True):
    id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this registry.",
    )
