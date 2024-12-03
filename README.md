# FEA Granular Certificate Demonstration Registry
An open-source platform to demonstrate the capabilities of a Granular Certificate registry that conforms to the EnergyTag Standards and API specification.

### Operation
The GC Registry is designed to be downloaded and operated locally either through a Docker container, or through manual package loading for development purposes.
In addition, a persistent instance will be available on GCP for non-technical users to interact with the front end.

Dependency management is handled through Poetry - on first use, run `poetry install` to initialise the required packages.

To get started interfacing with the GC Registry container, follow these steps to get started, using your IDE and API messenger of choice:
- Make sure you have the Docker daemon running, either through Docker desktop or the CLI.
- On first use, from the root directory run `docker compose -f compose.override.yml up --build` to build the image and run the container cluster. The cluster is composed of four containers:
    - `gc_registry` - the FastAPI app and backend services for the registry
    - `eventsotre` - an open-source streaming database that sequentially records registry events immutably
    - `postgres_db_write` - a Postgres database container using the official image that receives write operations from the registry
    - `postgres_db_read` - the parallel read Postgres instance that is written to simultaneously to the write instance, in order to optimise the concurrent processing of read operations without being detrimental to the performance of write operations.
- By default, the container port mappings are: 
    - The `gc_registry` FastAPI app - `8000`
    - The `eventstore` instance GUI - `2113`
    - The Postgres write intance - `5436`
    - The Postgres read instance - `5438` 
- Documentation comes in two flavours:
    - `localhost:8000/docs` - Swagger-style schema and endpoint descriptions that allows basic interaction with API
    - `localhost:8000/redoc` - alternative, non-interactive documentation from Redocly that is more human-readable than Swagger
- This repository uses a [makefile](Makefile) for quick access to convenience functions that are common across both users and developers. For instance, `make dev` will quickly call Docker compose to load up the container cluster. 
- Initially, the database instances will contain no elements. To get started quickly, we recommend seeding the database with some example User, Account, Device, and GC Bundle entities courtesy of Elexon (the UK aggregator of electricity system data) with the command `make db.seed`.

### Interfacing with the Registry

Each entity has the four basic crud operation endpoints accessible through the lower case singular name of the entity as the router and the operation or ID as the suffix. For example, either through Postman to `localhost:8000` or through a notebook with `client = httpx.Client("localhost:8000)` 
- `GET(account/1)` will return the account with ID 1, which in this case would be first account created on the registry as the integer ID primary keys are unique and serial across each entity.
- Creating an entity is possible like so:
    ```python
    from gc_registry.account.schemas import AccountBase
    account = AccountBase(account_name="Example Account", user_ids=[1], account_whitelist=[1])
    client.post("account/create", data=account.model_dump_json())
    ```
    This will create an account with the name `Example Account`, belonging to the user with ID `1`, and has whitelisted the account with ID `1` to receive GC Bundles from.
- Querying certificates is done through the `certificates/query` POST endpoint, and allows for advanced requests to be expressed through the `CertificateQuery` object, the schema for which can be found in the docs.
- To enforce a safe workflow whereby registry users do not unintentially apply certificate lifecycle actions such as `transfer` and `cancel` to bundles using blind queries, these actions only accept lists of certificate bundle IDs (not to be confused with the bundle _range_ IDs that identify the individual Wh within each bundle). This encourages users to first run a `query`, confirm that the GC Bundles returned are those that they wish to operate on, and then pass the bundle IDs to the mutation endpoint to perform the intended action on those GC bundles.

### Validation and Constraints

The registry contains numerous validation steps to ensure that double counting risk is mitigated. Some additional mechanisms that have been included to mirror the operation of existing registries include:
- Accounts can only transfer GC Bundles to another account if the target account has whitelisted the source account. This can be achieved through the `account/update_whitelist` endpoint.


### Technology choices

The main technological choices for the application include:

- Language: [Python](https://www.python.org/)
- Framework: [FastAPI](https://fastapi.tiangolo.com/)
- Database: [PostgreSQL](https://www.postgresql.org/) (Local instances)
- Models/types: [Pydantic](https://docs.pydantic.dev/latest/) (As specified in the EnergyTag API specification code)
- ORM: [SQLModel](https://sqlmodel.tiangolo.com/) (abstraction of [SQLAlchemy](https://www.sqlalchemy.org/))
- Frontend: [React](https://react.dev/)/[Node.js](https://nodejs.org/en) with [Axios](https://axios-http.com/docs/intro) for HTTP requests to FastAPI backend

Development tools:

- Dependency/Environment management: [Poetry](https://python-poetry.org/)
- Database migrations: [Alembic](https://alembic.sqlalchemy.org/en/latest/)
- Test runner: [Pytest](https://docs.pytest.org/en/8.0.x/)
- Code linting/formatting: [Ruff](https://docs.astral.sh/ruff/)
- CI/CD: [GitHub Actions](https://github.com/features/actions)
- Versioning: [Python Semantic release](https://python-semantic-release.readthedocs.io/en/latest/)
- Deployment: [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

## Further documentation

| I want to know about...              |                                  |
|--------------------------------------|----------------------------------|
| [Development](docs/DEVELOPMENT.md)   | Linting, formatting, testing etc |
| [Deployment](docs/DEPLOYMENT.md)     | General deployment docs          |
| [Contributing](docs/CONTRIBUTING.md) | Our processes for contributors   |
| [Change Log](./CHANGELOG.md)         | Log of code changes              |





