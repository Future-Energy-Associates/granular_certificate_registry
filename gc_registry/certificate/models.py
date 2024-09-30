import datetime
import uuid
from typing import List, Union

from sqlmodel import Field, SQLModel

from gc_registry.certificate.schemas import (
    GranularCertificateActionBase,
    GranularCertificateBundleBase,
)

# issuance_id a unique non-sequential ID related to the issuance of the entire bundle.
# This can also be specified as a concat of device-startdate-enddate.
# whereas the range of GC IDs within the bundle are unique sequential integers
# that allow the bundle to be split into the underlying GCs. Future splits of the
# bundle will retain the original bundle issuance ID.


class TemporalBase(SQLModel):
    created_at: datetime.datetime = Field(default=datetime.datetime.utcnow())


class GranularCertificateBundle(
    GranularCertificateBundleBase, TemporalBase, table=True
):
    id: uuid.UUID = Field(
        primary_key=True,
        default=uuid.uuid4,
        description="A unique ID assigned to this certificate bundle.",
    )


# A Transfer object is specified by a User, and is stored in a transaction table that
# lists all transfers and cancellations between accounts for audit purposes

# "transfer", "recurring_transfer", "cancel", "claim", "withdraw"


class GranularCertificateAction(
    GranularCertificateActionBase, TemporalBase, table=True
):
    action_id: int = Field(
        primary_key=True,
        default=None,
        description="A unique ID assigned to this action.",
    )


class GranularCertificateActionResponse(GranularCertificateActionBase):
    action_response_status: str = Field(
        description="Specifies whether the requested action has been accepted or rejected by the registry."
    )


class GranularCertificateQueryResponse(GranularCertificateActionResponse):
    filtered_certificate_bundles: Union[List[GranularCertificateBundle], None]
