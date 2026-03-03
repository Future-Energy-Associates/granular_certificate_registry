GC lifecycle management functionality, encompassing issuance, transfer, cancellation,
claiming, withdrawal, reservation, import, and lineage tracking of GC Bundles.

Filtering of GC Bundles for action implementation and queries should be flexible for
the end user and accommodate any combination of the search parameters below for a
specific Account:

- **Issuance IDs** — Returns all GC Bundles matching any of the specified Issuance IDs. Each Issuance ID is implicitly scoped to a single Device and time period.
- **Certificate Time Period** — Returns all GC Bundles issued for generation that occurred within the specified start and end datetime range (maximum 30-day window). If no Device is specified, results can include GC Bundles from multiple Devices.
- **Energy Source** — Returns all GC Bundles issued for generation derived from the specified energy source type.
- **Production Device ID** — Returns all GC Bundles issued to the specified production Device.
- **Certificate Bundle Status** — Returns all GC Bundles with the specified lifecycle status (Active, Cancelled, Claimed, Expired, Withdrawn, Locked, Reserved, Bundle Split, or Cancelled for Storage).

GC Bundles can also be queried in a full view that includes issuance metadata and
production Device attributes alongside the certificate bundle fields. Certificate
lineage can be retrieved for any bundle, providing a complete audit trail of the
actions that have been performed on it and its ancestors.

GC Bundles may be imported from external registries via CSV or JSON file upload,
and will be associated with a Device and Account within the registry. Issuance
metadata can be created separately to record the regulatory and procedural context
under which GC Bundles were issued.
