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
	docker compose run --rm gc_registry sh -c 'echo "Checking for multiple heads..." && \
		HEADS_COUNT=$$(alembic heads | wc -l) && \
		if [ "$$HEADS_COUNT" -gt 1 ]; then \
			echo "Multiple heads detected." && \
			LATEST_HEAD=$$(alembic heads | head -n1 | sed "s/ (head)//" | sed "s/ (effective head)//" | tr -d " \\r\\n") && \
			echo "Keeping $$LATEST_HEAD as head" && \
			alembic heads | tail -n +2 | while IFS= read -r other_head; do \
				other_head=$$(echo "$$other_head" | sed "s/ (head)//" | sed "s/ (effective head)//" | tr -d " \\r\\n") && \
				echo "Processing: $$other_head" && \
				MIGRATION_FILE=$$(find /code/gc_registry/core/alembic/versions -type f -name "*.py" ! -path "*/__pycache__/*" -exec grep -l "$$other_head" {} +) && \
				if [ -n "$$MIGRATION_FILE" ]; then \
					echo "Updating $$MIGRATION_FILE to point to $$LATEST_HEAD" && \
					for FILE in $$MIGRATION_FILE; do \
						sed -i "s/^down_revision.*\$$/down_revision: str | None = '\''$$LATEST_HEAD'\''/" "$$FILE"; \
						sed -i "s/^branch_labels.*\$$/branch_labels: str | Sequence[str] | None = None/" "$$FILE"; \
						echo "Updated $$other_head to follow $$LATEST_HEAD in $$FILE"; \
					done; \
				else \
					echo "Warning: Could not find migration file for $$other_head"; \
				fi; \
			done && \
			echo "Head resolution completed. Running upgrade..." && \
			alembic upgrade head; \
		else \
			echo "No multiple heads detected. No fix needed."; \
		fi'

.PHONY: db.fix.merge
db.fix.merge:
	docker compose run --rm gc_registry sh -c 'echo "Checking for multiple heads..." && \
		HEADS_COUNT=$$(alembic heads | wc -l) && \
		if [ "$$HEADS_COUNT" -gt 1 ]; then \
			echo "Multiple heads detected. Using merge strategy..." && \
			alembic merge heads -m "merge_multiple_heads" && \
			echo "Heads merged successfully." && \
			alembic upgrade head && \
			echo "Please commit the newly generated merge migration file."; \
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
		docker volume rm granular_certificate_registry_eventstore-volume-data && \
		docker volume rm granular_certificate_registry_eventstore-volume-logs && \
		make db.update

.PHONY: db.test.migrations
db.test.migrations:
	make db.reset && \
	docker compose run --rm gc_registry alembic downgrade base

.PHONY: db.seed
db.seed:
	docker compose run --rm gc_registry poetry run seed-db

.PHONY: db.seed.elexon
db.seed.elexon:
	docker compose run --rm gc_registry poetry run seed-db-elexon

.PHONY: dev
dev:
	docker compose up
