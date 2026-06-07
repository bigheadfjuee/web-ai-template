# postgres-db Specification

## Purpose

TBD - created by archiving change 'user-management-crud'. Update Purpose after archive.

## Requirements

### Requirement: PostgreSQL 16 service in Compose

The `docker-compose.yml` SHALL include a `postgres` service using the `postgres:16-alpine` image with a named volume `postgres_data` for data persistence across `docker compose down` restarts. The service SHALL expose port `5432` on the internal Compose network and SHALL define a healthcheck so dependent services can wait for readiness.

#### Scenario: Postgres service starts and is healthy

- **WHEN** `docker compose up` is run from the repo root
- **THEN** the `postgres` service starts, the healthcheck passes within 30 seconds, and `docker compose ps` shows the `postgres` container as healthy

#### Scenario: Data persists across restarts

- **WHEN** a user row is inserted and then `docker compose down` (without `-v`) is run, followed by `docker compose up`
- **THEN** the user row is still present in the database


<!-- @trace
source: user-management-crud
updated: 2026-06-07
code:
  - backend/app/routers/users.py
  - frontend/src/App.vue
  - backend/app/config.py
  - backend/app/main.py
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/alembic.ini
  - backend/app/schemas/user.py
  - backend/alembic/script.py.mako
  - backend/app/models/user.py
  - backend/app/models/__init__.py
  - backend/alembic/README
  - docker-compose.yml
  - frontend/src/views/UsersView.vue
  - backend/app/schemas/__init__.py
  - frontend/src/api/users.ts
  - backend/alembic/versions/0001_create_users_table.py
  - backend/app/routers/__init__.py
  - backend/uv.lock
  - backend/Dockerfile
  - backend/pyproject.toml
-->

---
### Requirement: SQLAlchemy 2 async engine and session factory

The `backend/app/db.py` module SHALL replace `class Base(DeclarativeBase)` with `from sqlmodel import SQLModel` and expose `SQLModel.metadata` as the authoritative metadata object used by Alembic's `env.py` `target_metadata`. The async engine, `AsyncSessionLocal`, and `get_db` dependency SHALL remain functionally identical — only the metadata source changes.

#### Scenario: SQLModel.metadata used by Alembic env

- **WHEN** `backend/alembic/env.py` imports `target_metadata` from `app.db`
- **THEN** `target_metadata` is `SQLModel.metadata` and contains the `users` table definition after `app.models` is imported


<!-- @trace
source: sqlmodel-db-layer
updated: 2026-06-07
code:
  - backend/app/schemas/__init__.py
  - backend/alembic/versions/0001_create_users_table.py
  - backend/pyproject.toml
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/app/routers/users.py
  - backend/uv.lock
  - backend/app/schemas/user.py
  - backend/app/models/user.py
-->

---
### Requirement: Alembic migration for users table

The Alembic migration `0001_create_users_table` SHALL be updated so that its `upgrade()` function uses dialect-agnostic SQLAlchemy types only: `sa.Uuid` for the `id` column (no `server_default`), `sa.String(128)` for `username`, `sa.String(256)` for `email`, and `sa.DateTime(timezone=True)` for `created_at` and `updated_at` (no `server_default`). The `pgcrypto` extension creation and `gen_random_uuid()` function reference MUST be removed. The `downgrade()` function remains `DROP TABLE IF EXISTS users`. Running `alembic upgrade head` on a fresh database MUST succeed and produce a `users` table; running `alembic downgrade -1` MUST drop it.

#### Scenario: Migration applies without PostgreSQL extensions

- **WHEN** `alembic upgrade head` is run against a fresh PostgreSQL database without the `pgcrypto` extension pre-installed
- **THEN** the migration exits with status `0` and the `users` table is created with columns `id`, `username`, `email`, `created_at`, `updated_at`

#### Scenario: Migration is reversible

- **WHEN** `alembic downgrade -1` is run after a successful `alembic upgrade head`
- **THEN** the `users` table is dropped and `alembic_version` records no applied revisions


<!-- @trace
source: sqlmodel-db-layer
updated: 2026-06-07
code:
  - backend/app/schemas/__init__.py
  - backend/alembic/versions/0001_create_users_table.py
  - backend/pyproject.toml
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/app/routers/users.py
  - backend/uv.lock
  - backend/app/schemas/user.py
  - backend/app/models/user.py
-->

---
### Requirement: Automatic migration on backend container start

The backend container's start command SHALL run `alembic upgrade head` before launching uvicorn, so that the database schema is always current when the API becomes available. The backend Compose service SHALL declare `depends_on` with `condition: service_healthy` pointing to the `postgres` service.

#### Scenario: Backend waits for postgres healthcheck before starting

- **WHEN** `docker compose up` is run from a clean state
- **THEN** the backend container does not start uvicorn until the postgres healthcheck passes; `alembic upgrade head` completes with exit status `0` before uvicorn binds to port `8000`

<!-- @trace
source: user-management-crud
updated: 2026-06-07
code:
  - backend/app/routers/users.py
  - frontend/src/App.vue
  - backend/app/config.py
  - backend/app/main.py
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/alembic.ini
  - backend/app/schemas/user.py
  - backend/alembic/script.py.mako
  - backend/app/models/user.py
  - backend/app/models/__init__.py
  - backend/alembic/README
  - docker-compose.yml
  - frontend/src/views/UsersView.vue
  - backend/app/schemas/__init__.py
  - frontend/src/api/users.ts
  - backend/alembic/versions/0001_create_users_table.py
  - backend/app/routers/__init__.py
  - backend/uv.lock
  - backend/Dockerfile
  - backend/pyproject.toml
-->