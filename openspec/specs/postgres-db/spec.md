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

The backend SHALL use SQLAlchemy 2 with async support (`sqlalchemy[asyncio]`) and the `asyncpg` driver. The async engine and `AsyncSessionLocal` session factory SHALL be defined in `backend/app/db.py`. The engine SHALL be created from the `DATABASE_URL` setting in `app/config.py` and torn down during FastAPI's lifespan shutdown.

#### Scenario: Session factory provides async sessions

- **WHEN** a FastAPI route handler calls the `get_db` dependency
- **THEN** it receives an `AsyncSession` connected to the PostgreSQL database; the session is closed after the request completes


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
### Requirement: Alembic migration for users table

The backend SHALL use Alembic for schema management. A migration `0001_create_users_table` SHALL create the `users` table with columns: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `username VARCHAR(128) UNIQUE NOT NULL`, `email VARCHAR(256) UNIQUE NOT NULL`, `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`, `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`. Running `alembic upgrade head` SHALL apply the migration; running `alembic downgrade -1` SHALL drop the table.

#### Scenario: Migration applies cleanly

- **WHEN** `alembic upgrade head` is run against an empty database
- **THEN** the `users` table exists with all five columns and their constraints; the `alembic_version` table records the migration as applied

#### Scenario: Migration is reversible

- **WHEN** `alembic downgrade -1` is run after `alembic upgrade head`
- **THEN** the `users` table is dropped and `alembic_version` records no applied revisions


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