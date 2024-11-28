from pydantic import BaseModel
from sqlmodel import Field

from gc_registry import utils
from gc_registry.certificate.schemas import (
    GranularCertificateActionBase,
    GranularCertificateBundleBase,
    IssuanceMetaDataBase,
)
from gc_registry.core.models.base import CertificateStatus

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


class GranularCertificateAction(GranularCertificateActionBase, table=True):
    id: int | None = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class IssuanceMetaData(IssuanceMetaDataBase, utils.ActiveRecord, table=True):
    id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this registry.",
    )
