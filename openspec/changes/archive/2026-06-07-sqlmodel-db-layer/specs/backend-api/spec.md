## MODIFIED Requirements

### Requirement: SQLAlchemy and Alembic dependencies

The `backend/pyproject.toml` SHALL declare `sqlmodel>=0.0.21` as a runtime dependency in addition to the existing `alembic`, `asyncpg`, and `pydantic[email]` entries. The direct `sqlalchemy[asyncio]` entry SHALL be retained (SQLModel re-exports it but the explicit pin keeps the version locked). Running `uv sync --frozen` after updating the lockfile MUST install all packages without error, and `from sqlmodel import SQLModel` MUST be importable.

#### Scenario: SQLModel importable after sync

- **WHEN** `uv sync --frozen` is run after `uv lock` has recorded `sqlmodel`
- **THEN** the command exits with status `0` and `uv run python -c "from sqlmodel import SQLModel; print('ok')"` prints `ok`
