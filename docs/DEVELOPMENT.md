# FEA GC Registry - Development

We use [Poetry](https://python-poetry.org/) for dependency/environment management. To get started with local development, ensure you have poetry installed globally on your system. The quickest way to do so is using:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
Alternative install methods are available [here](https://python-poetry.org/docs/#installation).

In order to run tests and make contributions to this codebase, please install the required development dependencies using:
```bash
poetry install --with dev
```
This will set up an isolated virtual environment and install all the dependencies to help with developing the application.

You can now lint & format the code (with ruff), run static type-checking (with mypy) and run the tests (with pytest) using the relevant commands below:
```bash
make lint           # Lint the source files
make lint.fix       # Lint and fix lint problems
make format         # Format source files
make typecheck      # Run Static type-checking
make test           # Run tests within Docker container
make test.local     # Run tests using local poetry environment
```

## Database Migrations

We use [Alembic](https://alembic.sqlalchemy.org/en/latest/) to manage the database schema migrations.

### Updating the database to the latest migration

```bash
make db.update
```

### Creating a new migration

When we change the data models of the database we will need to run a database migration.

#### 1. Run a database locally with the *old* schema

First you need to have a database in the state *before* the migration you want to apply.

Make sure your feature branch is up-to-date with the `dev` branch and run `make db.update`

#### 2. Change the database models

Edit the [models.py](../gc_registry/datamodel/schemas) file to reflect the changes you
want to make to the schema.

#### 3. Generate the migration code

In most cases, you can have alembic generate a migration automatically:

```bash
make db.revision NAME="name_of_migration"
```
_N.B. No spaces in the name of the migration_

Make sure that the generated code makes sense. Adjust if needed.

#### 4. Run migration script

Run your latest migration:

```bash
make db.update
```

Make sure everything looks good in the database.

#### 5. Commit the migration

Commit the migration(s) to the repo, make a pull request and tag someone for review.

## Testing

We test all our code with the following approaches:

- **Unit testing**: Testing application logic at the individual function/class method level to ensure all code paths are tested.
- **Integration testing**: Testing higher level code (code that calls other code) runs as expected.

Of particular interest - integration testing ensures our API endpoints run/return as expected.

We use [pytest](https://docs.pytest.org/en/8.0.x/) to run our unit/integration tests. The test files are all located within the `tests` directory and can be run within a docker container using: `make test`.

## Pre-commits for linting, formatting and type-checking

To save you from constantly having to lint, format and type-check while you are developing we make use of a tool called [pre-commit](https://pre-commit.com/).

Additionally, we have set rules for pre-commit to check for committing large files, yaml and toml syntax checking as well as trailing whitespace characters.

When you install it, it runs right before making a commit in git. This way it ensures that the code is consistent and formatted even before it is committed.

You can find a file `.pre-commit-config.yaml` with configurations at the root of the project.

### Install pre-commit to run automatically

`pre-commit` is already part of the development dependencies of the project.

After having the `pre-commit` tool installed and available, you need to "enable" it in the local repository, so that it runs automatically before each commit.

Using Poetry, you could do it with:

```bash
❯ poetry run pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

Now whenever you try to commit, e.g. with:

```bash
git commit
```

...pre-commit will run and check and format the code you are about to commit, and will ask you to add that code (stage it) with git again before committing.

Then you can `git add` the modified/fixed files again and now you can commit.

### Running pre-commit hooks manually

you can also run `pre-commit` manually on all the files, you can do it using Poetry with:

```bash
❯ poetry run pre-commit run --all-files
check for added large files..............................................Passed
check toml...............................................................Passed
check yaml...............................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
lint/format/typecheck....................................................Passed
```

## Versioning

Automatic versioning for the application is handled using [Python Semantic Release](https://python-semantic-release.readthedocs.io/en/latest/index.html). This runs via the GitHub Action on pushes to the `main` branch.

To trigger a major, minor or patch version update, you need simply issue a commit message containing the appropriate prefix. See [here](https://python-semantic-release.readthedocs.io/en/latest/configuration.html#commit-parser-options-dict-str-any) for more details.

The version is updated, a new git tag is created and a new GitHub release is made along with a changelog update.

Manual versioning is of course still possible - but can be a bit brittle. The version strings in `gc_registry/__init__.py` & `pyproject.toml`, the git tag and changelog all need to reference the same version.

## Continuous Integration (CI)

We use GitHub Actions to handle CI which runs on every push to the repository, regardless of which git branch you are on. The CI workflow that runs in GitHub Actions can be found [here](../.github/workflows/ci.yml).

The CI workflow installs the same versions of Python/Poetry as the project and installs the development dependencies before running linting, type-checking and running the tests.

if you have an active pull request associated with a branch on GitHub, a failure in any part of the workflow will notify you and prevent you from merging the pull request.

The CI workflow runs [`gitleaks`](https://github.com/gitleaks/gitleaks-action?tab=readme-ov-file) to make sure that no secrets are accidently leaked.

## Deployment

The application is deployed to GCP using the `app.yml` file using gcloud cli. Once installed you can follow these commands:

1. Install gcloud cli tool 

```
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")

& $env:Temp\GoogleCloudSDKInstaller.exe
```
Or download the Google Cloud CLI installer at https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe

2. Login to GCP by running `gcloud init` from the root of the repo.

3. Follow the setup process in the terminal and select the `demo-registry` project when prompted.

4. Deploy app `gcloud app deploy api_service.yml`. Make sure to check the docker install runs successfully and the API is accessible, by testing locally before running this command.

5. To connect to the service via SSH you can run `gcloud app instances ssh <Instance-ID> --service=default --version=<latest-version>` you'll then need to run `docker exec -it <CONTAINER_ID_OR_NAME> sh` to access the docker container. Use `gcloud app instances list` to list instances.

### Eventstore deployment

This uses GCP kubernetes engine

1. Create instance via GCP Kubernetes Engine

2. Auth with service `gcloud container clusters get-credentials registry-eventstore --region=europe-north1`

3. `kubectl apply -f deployment\eventstore_deploy.yml`

3. `kubectl apply -f deployment\eventstore_service.yml`

4. Get the IP `kubectl get service eventstore-service`


### Steps to Resolve CrashLoopBackOff for EventStore

1. Inspect Pod Logs: View logs to identify the source of the error (e.g., unrecognized options) `kubectl logs eventstore-7994d68f8c-mxp7x -n default`

2. List All Environment Variables in the Pod: Identify conflicting environment variables like ServiceServicePort: `kubectl exec -it eventstore-7994d68f8c-mxp7x -n default -- printenv`

3. Disable Service Links: Prevent Kubernetes from injecting unwanted service environment variables. `kubectl edit deployment eventstore -n default` and add the following under spec.template.spec `enableServiceLinks: false`

4. Restart Deployment: Apply changes and restart the pods `kubectl rollout restart deployment eventstore -n default`

