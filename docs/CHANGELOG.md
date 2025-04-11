# Change Log

Tracks changes between releases following the semantic versioning outlined in the development documentation.

### v. 0.2.2

**New Features**
- Adds `GET /users/me` and `GET /users/me/accounts` to retrieve the logged in user and its linked accounts
- Adds `GET /accounts/{account_id}/users` to retrieve the users linked to an account
- Adds `GET /accounts/{account_id}/certificates` to retrieve the certificates linked to an account
- Adds `GET /accounts/{account_id}/devices` to retrieve the devices linked to an account
- Changes authentication to use the user's email address rather than user name

### v. 0.2.1

**New Features**
- Refactor account whitelisting to use a link table between source and target accounts to facilitate easier 
retrieval of inverse whitelists - necessary for the frontend to display to a user which accounts they may transfer to

**Fixes**
- Adds `make eventstore.reset` to reset the eventstore

### v. 0.2.0

**New Features**
- Adds user access controls via OAuth2, built-in to the FastAPI middleware
- Endpoints require a bearer token retrievable through `auth/login` and validate access based on role

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