from hashlib import sha256

from esdbclient import EventStoreDBClient
from sqlalchemy.orm.session import Session

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
        f"{gc_bundle.model_dump_json(exclude='id')}{nonce}".encode()
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


def split_certificate_bundle(
    gc_bundle: GranularCertificateBundle,
    size_to_split: int,
    write_session: Session,
    read_session: Session,
    esdb_client: EventStoreDBClient,
):
    """Given a GC Bundle, split it into two child bundles and return them.

    Example operation: a parent bundle with 100 certificates, when passed a
    size_to_split of 25, will return the first child bundle with 25 certificates
    and the second bundle with 75. Each of these will be created separately as
    new bundles, with the same issuance ID of the parent bundle, and the parent
    bundle will be marked as deleted but preserved in the database for audit
    and lineage purposes.

    Args:
        gc_bundle (GranularCertificateBundle): The parent GC Bundle
        size_to_split (int): The number of certificates to split from
            the parent bundle.

    Returns:
        tuple[GranularCertificateBundle, GranularCertificateBundle]: The two child GC Bundles
    """

    assert size_to_split > 0, "The size to split must be greater than 0"
    assert (
        size_to_split < gc_bundle.bundle_quantity
    ), "The size to split must be less than the total certificates in the parent bundle"

    # Create two child bundles
    gc_bundle_child_1 = GranularCertificateBundleBase(**gc_bundle.model_dump())
    gc_bundle_child_2 = GranularCertificateBundleBase(**gc_bundle.model_dump())

    # Update the child bundles with the new quantities
    gc_bundle_child_1.bundle_quantity = size_to_split
    gc_bundle_child_1.bundle_id_range_end = (
        gc_bundle_child_1.bundle_id_range_start + size_to_split
    )
    gc_bundle_child_1.hash = create_bundle_hash(gc_bundle_child_1, gc_bundle.hash)

    gc_bundle_child_2.bundle_quantity = gc_bundle.bundle_quantity - size_to_split
    gc_bundle_child_2.bundle_id_range_start = gc_bundle_child_1.bundle_id_range_end + 1
    gc_bundle_child_2.hash = create_bundle_hash(gc_bundle_child_2, gc_bundle.hash)

    # Mark the parent bundle as deleted
    gc_bundle.delete(write_session, read_session, esdb_client)

    # Write the child bundles to the database
    db_gc_bundle_child_1 = GranularCertificateBundle.create(
        gc_bundle_child_1, write_session, read_session, esdb_client
    )[0]
    db_gc_bundle_child_2 = GranularCertificateBundle.create(
        gc_bundle_child_2, write_session, read_session, esdb_client
    )[0]

    return db_gc_bundle_child_1, db_gc_bundle_child_2
