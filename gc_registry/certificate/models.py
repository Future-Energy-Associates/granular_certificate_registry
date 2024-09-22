import uuid
from enum import Enum

from sqlmodel import Field

from gc_registry import utils
from gc_registry.certificate.schemas import (
    GranularCertificateActionBase,
    GranularCertificateBundleBase,
    GranularCertificateRegistryBase,
)

# issuance_id a unique non-sequential ID related to the issuance of the entire bundle.
# This can also be specified as a concat of device-startdate-enddate.
# whereas the range of GC IDs within the bundle are unique sequential integers
# that allow the bundle to be split into the underlying GCs. Future splits of the
# bundle will retain the original bundle issuance ID.


class GranularCertificateBundle(
    utils.ActiveRecord, GranularCertificateBundleBase, table=True
):
    issuance_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="""A unique identifier assigned to the GC Bundle at the time of issuance.
        If the bundle is split through partial transfer or cancellation, this issuance ID remains unchanged across each child GC Bundle.""",
    )


# A Transfer object is specified by a User, and is stored in a transaction table that
# lists all transfers and cancellations between accounts for audit purposes

# "transfer", "recurring_transfer", "cancel", "claim", "withdraw"


class GranularCertificateAction(
    GranularCertificateActionBase, utils.ActiveRecord, table=True
):
    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class GranularCertificateRegistry(
    GranularCertificateRegistryBase, utils.ActiveRecord, table=True
):
    id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this registry.",
    )
