## Why

The template currently has no persistence layer — every restart loses state and there is no way to manage application users. Adding PostgreSQL with full CRUD user management gives downstream projects a working data model and admin surface to build on from day one.

## What Changes

- Add a PostgreSQL 16 service to the Docker Compose stack; the backend connects to it via an `DATABASE_URL` environment variable.
- Add SQLAlchemy 2 (async) + asyncpg as backend dependencies; introduce Alembic for schema migrations.
- Introduce a `User` model with fields: `id` (UUID PK), `username` (unique, non-null), `email` (unique, non-null), `created_at`, `updated_at`.
- Expose a REST router under `/api/users` implementing full CRUD:
  - `POST /api/users` — create user
  - `GET /api/users` — list all users (paginated: `skip` + `limit` query params)
  - `GET /api/users/{id}` — get single user by UUID
  - `PUT /api/users/{id}` — update username and/or email
  - `DELETE /api/users/{id}` — delete user; returns 204
- Add a Vue 3 Users page in the frontend SPA that lists users and provides Create / Edit / Delete actions via the REST API.
- Wire the new frontend page into the existing `App.vue` as a simple tab or section alongside the existing health-check view.
- **BREAKING**: `docker-compose.yml` gains a new `postgres` service; existing `docker compose up` invocations will pull the postgres image on first run.

## Non-Goals

- No authentication or authorization — all CRUD endpoints are open; auth is a future change.
- No password / credentials field on the User model — only `username` and `email`.
- No frontend routing library (Vue Router) — the Users page is added as a toggled section in `App.vue`.
- No search, filter, or sort beyond the `skip`/`limit` pagination on the list endpoint.
- No soft-delete — `DELETE` is a hard delete.
- No email uniqueness enforcement beyond the database unique constraint (no verification flow).

## Capabilities

### New Capabilities

- `postgres-db`: PostgreSQL 16 service in Compose, connection wiring via `DATABASE_URL`, SQLAlchemy async engine, Alembic migrations, `User` model.
- `user-api`: FastAPI CRUD router at `/api/users` backed by PostgreSQL, with Pydantic request/response schemas.
- `user-management-ui`: Vue 3 Users page in the SPA that lists, creates, edits, and deletes users via the REST API.

### Modified Capabilities

- `backend-api`: New dependency group (SQLAlchemy, asyncpg, alembic) added to `pyproject.toml`; app factory wired with a database lifespan; new router registered at `/api/users`.
- `container-deploy`: `docker-compose.yml` gains `postgres` service with a named volume; nginx/backend service dependencies updated; backend gains `DATABASE_URL` env var.

## Impact

- Affected specs: new — `postgres-db`, `user-api`, `user-management-ui`; modified — `backend-api`, `container-deploy`.
- Affected code:
  - New:
    - `backend/app/db.py`
    - `backend/app/models/user.py`
    - `backend/app/schemas/user.py`
    - `backend/app/routers/users.py`
    - `backend/alembic.ini`
    - `backend/alembic/env.py`
    - `backend/alembic/versions/0001_create_users_table.py`
    - `frontend/src/views/UsersView.vue`
    - `frontend/src/api/users.ts`
  - Modified:
    - `backend/pyproject.toml`
    - `backend/uv.lock`
    - `backend/app/main.py`
    - `backend/app/config.py`
    - `backend/app/models/__init__.py`
    - `backend/app/schemas/__init__.py`
    - `backend/app/routers/__init__.py`
    - `frontend/src/App.vue`
    - `docker-compose.yml`
  - Removed: (none)
