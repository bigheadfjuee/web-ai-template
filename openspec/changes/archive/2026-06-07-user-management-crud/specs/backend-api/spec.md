## ADDED Requirements

### Requirement: SQLAlchemy and Alembic dependencies

The `backend/pyproject.toml` SHALL declare `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `alembic`, and `pydantic[email]` as runtime dependencies. Running `uv sync --frozen` after updating the lockfile MUST install all new packages without error.

#### Scenario: New dependencies install from updated lockfile

- **WHEN** `uv sync --frozen` is run after `uv lock` has recorded the new packages
- **THEN** the command exits with status `0` and `sqlalchemy`, `asyncpg`, `alembic`, and `email-validator` are importable from within the virtualenv

### Requirement: Database lifespan in app factory

The `create_app()` function in `backend/app/main.py` SHALL register a FastAPI lifespan context manager that creates the SQLAlchemy async engine on startup and disposes it on shutdown. The lifespan SHALL be the sole location where the engine is created.

#### Scenario: Engine created on startup

- **WHEN** the FastAPI application starts
- **THEN** the SQLAlchemy async engine is created and available to route handlers via the `get_db` dependency before the first request is served

### Requirement: /api/users router registered in app factory

The `create_app()` function SHALL include the users router so that all five CRUD endpoints are reachable after startup without any additional wiring.

#### Scenario: Users router reachable after startup

- **WHEN** the backend starts and a client sends `GET /api/users`
- **THEN** the response status is `200` (not `404`), confirming the router is registered
