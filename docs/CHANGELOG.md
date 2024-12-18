# Change Log

Tracks changes between releases following the semantic versioning outlined in the development documentation.

### v. 0.1.1

**New Features**
- Adds demo notebook taking the user through setting up and basic interactions with the registry

**Fixes**
- Bug with validating accounts linked to existing users on creation


### v. 0.1.0

**New Features**
- CRUD endpoints for all GC entities
- Implements GC lifecycle management functions including issuance against device measurement data from Elexon
- Transfers of GC bundles between accounts with whitelisting procedure
- Functionality for partial actions on GC bundles that result in split 'child' bundles
- All operations on entities are recorded as streaming events using EventStoreDB   

**Removes**
- Measurement records are not retained upon GC bundle issuance