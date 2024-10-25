from sqlmodel import Field

from gc_registry import utils
from gc_registry.certificate.schemas import (
    GranularCertificateActionBase,
    GranularCertificateBundleBase,
    IssuanceMetaDataBase,
)

# issuance_id a unique non-sequential ID related to the issuance of the entire bundle,
# specified as a concatenation of deviceID-EnergyCarrier-ProductionStartDatetime.
# The range of GC IDs within the bundle are unique sequential integers
# that allow the bundle to be split into the underlying GCs. Future splits of the
# bundle will retain the original bundle issuance ID.


class GranularCertificateBundle(
    utils.ActiveRecord, GranularCertificateBundleBase, table=True
):
    id: int | None = Field(
        primary_key=True,
        default=None,
        description="A unique, incremental integer ID assigned to this bundle.",
    )
    issuance_id: str = Field(
        primary_key=True,
        description="""A unique identifier assigned to the GC Bundle at the time of issuance.
        If the bundle is split through partial transfer or cancellation, this issuance ID
        remains unchanged across each child GC Bundle.""",
    )
    hash: str = Field(
        default=None,
        description="""A unique hash assigned to this bundle at the time of issuance,
        formed from the sha256 of the bundle's properties and, if the result of a bundle
        split, a nonce taken from the hash of the parent bundle.""",
    )


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
