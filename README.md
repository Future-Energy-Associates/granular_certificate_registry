# FEA Granular Certificate Demonstration Registry
An open-source platform to demonstrate the capabilities of a Granular Certificate registry that conforms to the EnergyTag Standards and API specification.

### Operation
The GC Registry is designed to be downloaded and operated locally either through a Docker container, or through manual package loading for development purposes.
In addition, a persistent instance will be available on GCP for non-technical users to interact with the front end.

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





