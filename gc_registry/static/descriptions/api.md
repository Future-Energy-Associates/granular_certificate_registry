This document outlines the EnergyTag API Specification to accompany Version 2 of
the EnergyTag Standard.
The functionality outlined within each API interaction represents the recommended
minimum required detail necessary to implement a consistent Granular Certificate
(GC) registry system.

The API is organised into the following sections:

- **Certificates** — GC lifecycle management including issuance, querying, transfer, cancellation, claiming, withdrawal, reservation, and import of GC Bundles. Certificate lineage tracking provides full auditability of GC Bundle provenance across all actions.
- **Storage** — Management of Storage Charge and Discharge Records, their allocation into matched pairs, and the issuance of Storage Discharge GC (SD-GC) Bundles against verified storage operations.
- **Measurements** — Submission of meter readings from production Devices, driving the issuance of GC Bundles against verified energy generation intervals.
- **Users** — Management of individuals affiliated with an Organisation. Users manage Accounts and are assigned roles that govern their access privileges.
- **Accounts** — Accounts hold GC Bundles issued from Devices and can transfer them to other whitelisted Accounts. Can be managed by one or more Users.
- **Devices** — Registration and management of production, consumption, or storage units against which GC Bundles or Storage Records are issued.
- **Authentication** — Login, JWT access token management, and API key creation for programmatic access.

Within the Certificates section, the definition of GCs as specified in the Create
Certificate POST request, alongside the filtering parameters required to instigate
query, transfer, and cancellation requests, will form core components of the standard
and impact the functionality of the registry the greatest. Subsequent sections
describing User, Account, and Device management are **recommendations
only** and do not form part of the standard, although terminology used therein is
referenced in the certificate definitions.

Where Universally Unique Identifiers (UUIDs) have been used, these can be replaced with
any consistent and unique identification mechanism preferred by the registry; for
example, concatenations of datetime and Device ID). It is recommended that GC Bundle
IDs remain represented as integers, or an initial string concatenated with an integer,
that can be both uniquely referenced and unambiguously incremented to simplify the
GC Bundle subdivision process.

All mutating operations are recorded as events in an append-only event store, ensuring
full traceability and auditability of all registry actions. Users authenticate via
JWT access tokens or API keys, and role-based access control determines the operations
each user is authorised to perform. Available roles, in descending order of privilege,
are: Admin, Production User, Trading User, Audit User, and Storage Validator.

Each API call defined below is to be interpreted as an instance of an object that is
stored by the registry upon receipt by a User, and can be updated as it moves from
received, through pending, to resolved within a transaction log uniquely identified
by an action ID. With this in mind, fields such as `action_completed_datetime` are
not to be interpreted as attributes supplied by the User, but fields that are
populated and updated by the registry as the request is processed.
This approach allows any and all actions to be queried and traced, with relevant
User access rights left to the discretion of the registry operator.
