#
# Shortcuts for build commands, linting, testing etc
#

SRC = gc_registry

.PHONY: lint
lint:
	poetry run ruff check $(SRC)

.PHONY: lint.fix
lint.fix:
	poetry run ruff check --fix $(SRC)

.PHONY: format
format:
	poetry run ruff format $(SRC)

.PHONY: typecheck
typecheck:
	poetry run mypy $(SRC)

.PHONY: test
test:
	docker compose run --no-deps --rm gc_registry pytest --cov-report term --cov-report html --cov=gc_registry

.PHONY: test.local
test.local:
	poetry run pytest --cov-report term --cov-report html --cov=gc_registry

.PHONY: workflow
workflow:
	poetry run pytest

.PHONY: pre-commit
pre-commit: lint.fix format typecheck

.PHONY: ci
ci: lint typecheck workflow

.PHONY: db.update
db.update:
	docker compose run --rm gc_registry alembic upgrade head

.PHONY: db.fix
db.fix:
	docker compose run --rm gc_registry /bin/sh -c '\
		echo "Checking for multiple heads..." && \
		if [ $$(alembic heads | wc -l) -gt 1 ]; then \
			echo "Multiple heads detected. Merging..." && \
			alembic merge heads && \
			echo "Heads merged successfully."; \
			alembic upgrade head; \
		else \
			echo "No multiple heads detected. No merge needed."; \
		fi'

.PHONY: db.revision
db.revision:
	make db.fix  && \
		echo "Creating new revision..." && \
		docker compose run --rm gc_registry alembic revision --autogenerate -m $(NAME) && \
		echo "Revision created successfully."

.PHONY: db.reset
db.reset:
	docker compose down && \
		docker volume rm granular_certificate_registry_postgres_data_read && \
		docker volume rm granular_certificate_registry_postgres_data_write && \
		make db.update

.PHONY: db.seed
db.seed:
	docker compose run --rm gc_registry poetry run seed-db

.PHONY: dev
dev:
	docker compose up
