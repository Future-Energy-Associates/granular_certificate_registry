from hashlib import sha256

from .models import (
    GranularCertificateBundle,
    GranularCertificateBundleBase,
)
from .schemas import GranularCertificateBundleCreate


def validate_transfer():
    pass


def create_bundle_hash(
    gc_bundle: GranularCertificateBundle | GranularCertificateBundleCreate,
    nonce: str = "",
):
    """
    Given a GC Bundle and a nonce taken from the hash of a parent bundle,
    return a new hash for the child bundle that demonstrates the child's
    lineage from the parent.

    To ensure that a consistent string representation of the GC bundle is
    used, a JSON model dump of the base bundle class is used to avoid
    automcatically generated fields such as the bundle's ID.

    Args:
        gc_bundle (GranularCertificateBundle): The child GC Bundle
        nonce (str): The hash of the parent GC Bundle

    Returns:
        str: The hash of the child GC Bundle
    """

    return sha256(
        f"{GranularCertificateBundleBase(**gc_bundle.model_dump())}{nonce}".encode()
    ).hexdigest()


def verifiy_bundle_lineage(
    gc_bundle_parent: GranularCertificateBundle,
    gc_bundle_child: GranularCertificateBundle,
):
    """
    Given a parent and child GC Bundle, verify that the child's hash
    can be recreated from the parent's hash and the child's nonce.

    Args:
        gc_bundle_parent (GranularCertificateBundle): The parent GC Bundle
        gc_bundle_child (GranularCertificateBundle): The child GC Bundle

    Returns:
        bool: Whether the child's hash can be recreated from the parent's hash
    """

    return (
        create_bundle_hash(gc_bundle_child, gc_bundle_parent.hash)
        == gc_bundle_child.hash
    )
