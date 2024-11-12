from hashlib import sha256

from gc_registry.certificate.models import (
    GranularCertificateBundle,
    GranularCertificateBundleBase,
)
from gc_registry.certificate.schemas import mutable_gc_attributes


def create_bundle_hash(
    gc_bundle: GranularCertificateBundle | GranularCertificateBundleBase,
    nonce: str | None = "",
):
    """
    Given a GC Bundle and a nonce taken from the hash of a parent bundle,
    return a new hash for the child bundle that demonstrates the child's
    lineage from the parent.

    To ensure that a consistent string representation of the GC bundle is
    used, a JSON model dump of the base bundle class is used to avoid
    automcatically generated fields such as the bundle's ID. In addition,
    only non-mutable fields are included such that lineage can be traced
    no matter the lifecycle stage the GC is in.

    Args:
        gc_bundle (GranularCertificateBundle): The child GC Bundle
        nonce (str): The hash of the parent GC Bundle

    Returns:
        str: The hash of the child GC Bundle
    """

    gc_bundle_dict = gc_bundle.model_dump_json(
        exclude=set(["id", "created_at", "hash"] + mutable_gc_attributes)
    )
    return sha256(f"{gc_bundle_dict}{nonce}".encode()).hexdigest()
