import uuid as uuid_pkg

from sqlmodel import Field

from src.models.certificate import GranularCertificateBundleBase

# issuance_id a unique non-sequential ID related to the issuance of the entire bundle.
# This can also be specified as a concat of device-startdate-enddate.
# whereas the range of GC IDs within the bundle are unique sequential integers
# that allow the bundle to be split into the underlying GCs. Future splits of the
# bundle will retain the original bundle issuance ID.


class GranularCertificateBundle(GranularCertificateBundleBase, table=True):
    issuance_id: uuid_pkg.UUID = Field(
        primary_key=True,
        default_factory=uuid_pkg.uuid4,
        description="""A unique identifier assigned to the GC Bundle at the time of issuance.
        If the bundle is split through partial transfer or cancellation, this issuance ID remains unchanged across each child GC Bundle.""",
    )
