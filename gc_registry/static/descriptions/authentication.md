Authentication and authorisation for registry access. Users authenticate via a login
endpoint using email and password credentials to receive a JWT access token, which
must be included in subsequent request headers.

For programmatic access, authenticated users can create named API keys with
configurable expiry dates. API keys are used in place of a username and password
in the request Authorization header. Users can list all of their active API keys
and deactivate individual keys by ID. Admins can deactivate any user's API key.
