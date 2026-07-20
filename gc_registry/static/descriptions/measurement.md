Submission and management of meter readings from production Devices. Meter readings
are submitted as CSV files containing interval-level usage data for a single Device,
and are validated before being persisted as Measurement Reports.

Upon successful submission, GC Bundles are automatically issued against the verified
energy generation intervals using the latest available issuance metadata. Individual
Measurement Reports can also be created, read, updated, and deleted via dedicated
CRUD endpoints. Updates and deletions require Admin privileges, as GC Bundles may
have already been issued against the readings.
