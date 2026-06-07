## Context

The template currently runs FastAPI with no persistence; the only data flow is a stateless `/api/health` response. This change adds PostgreSQL 16, SQLAlchemy 2 async, Alembic migrations, a `User` model, a `/api/users` CRUD router, and a Vue 3 Users page — turning the scaffold into a working user-management starting point.

Constraints:
- Package manager is `uv`; all new Python deps go into `pyproject.toml` and are locked into `uv.lock`.
- Docker Compose is the deployment surface; PostgreSQL must be a named Compose service.
- The frontend has no router library; the Users page is toggled as a section inside `App.vue`.
- No auth in scope; all endpoints are open.

## Goals / Non-Goals

**Goals:**
- PostgreSQL reachable from the backend over the internal Compose network as `postgres:5432`.
- Async SQLAlchemy engine created once at app startup (lifespan) and torn down on shutdown.
- Alembic migration that creates the `users` table with a single `alembic upgrade head` invocation.
- Full CRUD router at `/api/users` returning JSON; request/response shapes defined as Pydantic v2 models.
- Vue 3 Users page that calls the CRUD API and re-renders on every mutation.
- Existing `/api/health` endpoint and SPA shell unaffected.

**Non-Goals:**
- No authentication, sessions, or tokens.
- No password / credentials column on the `users` table.
- No Vue Router; no client-side routing.
- No search, sort, or filter beyond `skip`/`limit` pagination.
- No soft-delete; `DELETE` is hard.
- No frontend form validation library; native HTML5 `required` attributes suffice.

## Decisions

### SQLAlchemy 2 async with asyncpg driver

Use `sqlalchemy[asyncio]>=2.0` and `asyncpg` for the async PostgreSQL driver. The engine is created once in `backend/app/db.py` via `create_async_engine(DATABASE_URL)` and an `AsyncSessionLocal` session factory is exposed as a FastAPI dependency (`get_db`). Rationale: SQLAlchemy 2 async integrates naturally with FastAPI's async path functions and Alembic's migration tooling, avoiding a second ORM layer.

Alternative considered: `databases` + raw SQL. Rejected because it bypasses Alembic's migration management and forces manual schema tracking.

### Alembic for schema migrations

Alembic is initialized with `alembic init alembic` inside `backend/`. A single initial migration (`0001_create_users_table`) creates the `users` table. Migrations run inside the backend container via `alembic upgrade head` executed as a startup command before uvicorn, or manually by the developer. Rationale: Alembic is the standard SQLAlchemy migration tool; it pairs naturally with declarative models and produces reversible `downgrade()` stubs.

Decision: migrations run automatically at container startup — `CMD` in `backend/Dockerfile` becomes `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"`. This keeps the deploy flow simple for a template.

Alternative: a separate migration job or manual `docker exec`. Rejected for the template use case — one command to bring everything up is the goal.

### User model fields

`users` table columns: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `username VARCHAR(128) UNIQUE NOT NULL`, `email VARCHAR(256) UNIQUE NOT NULL`, `created_at TIMESTAMPTZ DEFAULT now()`, `updated_at TIMESTAMPTZ DEFAULT now()`. No password column (per Non-Goals). Rationale: UUID primary keys avoid sequential enumeration; `gen_random_uuid()` is built into PostgreSQL 13+.

### Pydantic v2 schemas split into request / response

- `UserCreate`: `username: str`, `email: EmailStr`
- `UserUpdate`: `username: str | None = None`, `email: EmailStr | None = None` (partial update — only non-None fields applied)
- `UserResponse`: `id: UUID`, `username: str`, `email: str`, `created_at: datetime`, `updated_at: datetime`

Pydantic v2's `model_config = ConfigDict(from_attributes=True)` enables ORM-mode serialization from SQLAlchemy model instances.

### PostgreSQL service in Compose with named volume

`docker-compose.yml` gains a `postgres` service using the official `postgres:16-alpine` image, a named volume `postgres_data` for persistence across restarts, and environment variables `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` set to `appuser`, `apppassword`, `appdb` (template-grade defaults, not production-safe). Backend's `DATABASE_URL` is `postgresql+asyncpg://appuser:apppassword@postgres:5432/appdb`. Rationale: alpine variant keeps image size small; named volume survives `docker compose down`.

Alternative: external managed database. Out of scope — this is a local template scaffold.

### Frontend Users page as toggled section in App.vue

A `<UsersView />` component is toggled with a simple boolean `showUsers` ref in `App.vue`. A tab bar with two buttons ("Health" / "Users") switches between the health-check view and the users view. API calls live in `frontend/src/api/users.ts` as typed fetch wrappers. Rationale: no Vue Router is in scope; a single boolean toggle is the simplest correct approach for two views.

### API client in users.ts (typed fetch, no library)

`frontend/src/api/users.ts` exports five functions: `listUsers(skip, limit)`, `getUser(id)`, `createUser(data)`, `updateUser(id, data)`, `deleteUser(id)`. Each wraps `fetch` with the correct method, `Content-Type: application/json`, and throws a typed `ApiError` on non-2xx responses. Rationale: no axios or tanstack-query is introduced — the template stays minimal; callers handle loading/error state themselves with `ref`.

## Implementation Contract

**Observable behaviors (acceptance):**

- `docker compose up --build` brings up postgres, backend, and nginx; `alembic upgrade head` runs automatically inside the backend container on startup before uvicorn binds.
- `curl -fsSk https://localhost/api/users` returns `200` with body `[]` (empty array) on a fresh database.
- `curl -fsSk -X POST https://localhost/api/users -H 'Content-Type: application/json' -d '{"username":"alice","email":"alice@example.com"}'` returns `201` with a JSON body containing `id` (UUID), `username`, `email`, `created_at`, `updated_at`.
- `curl -fsSk https://localhost/api/users/<uuid>` returns `200` with the user object; an unknown UUID returns `404` with `{"detail":"User not found"}`.
- `curl -fsSk -X PUT https://localhost/api/users/<uuid> -H 'Content-Type: application/json' -d '{"email":"newemail@example.com"}'` returns `200` with the updated object; `updated_at` is later than `created_at`.
- `curl -fsSk -X DELETE https://localhost/api/users/<uuid>` returns `204` with no body; a second DELETE on the same UUID returns `404`.
- Duplicate `username` or `email` on POST or PUT returns `409` with `{"detail":"Username or email already exists"}`.
- Opening `https://localhost/` in a browser and switching to "Users" renders the user list; creating, editing, and deleting a user re-fetches the list and the change is visible without a full page reload.
- The existing `GET /api/health` continues to return `{"status":"ok"}` with no change to response shape.

**Interfaces / data shapes:**

- `GET /api/users?skip=0&limit=100` → `200` `[UserResponse, ...]`; `skip` and `limit` default to `0` and `100`.
- `POST /api/users` body: `{"username": str, "email": str}` → `201` `UserResponse`
- `GET /api/users/{id}` → `200` `UserResponse` or `404`
- `PUT /api/users/{id}` body: `{"username"?: str, "email"?: str}` (at least one field required) → `200` `UserResponse` or `404` or `409`
- `DELETE /api/users/{id}` → `204` or `404`
- `UserResponse` shape: `{"id": "<uuid>", "username": str, "email": str, "created_at": "<ISO8601>", "updated_at": "<ISO8601>"}`

**Failure modes:**

- Backend cannot reach postgres at startup: uvicorn still starts (SQLAlchemy is lazy); the first request that touches the DB returns `500`. The backend container will restart if postgres is not yet ready — use `depends_on: postgres` with `condition: service_healthy` in Compose.
- `alembic upgrade head` fails (e.g., postgres not yet accepting connections): the backend container exits non-zero and Compose restarts it. Mitigation: postgres healthcheck in Compose; backend `depends_on` with `condition: service_healthy`.
- Duplicate username/email INSERT raises `asyncpg.UniqueViolationError`; the router catches `sqlalchemy.exc.IntegrityError` and returns `409`.

**Acceptance verification:**

- Manual: run the `curl` sequence above against the live stack; all status codes and response bodies MUST match.
- Manual: browser at `https://localhost/` — "Users" tab visible, CRUD operations update the list in place.
- `docker compose config` — `postgres` service present with `postgres_data` volume and healthcheck defined.

**Scope boundaries:**

- In scope: the files listed in the proposal Impact section, the five CRUD endpoints, the single `users` table migration, the Vue Users page.
- Out of scope: authentication, password fields, email verification, Vue Router, frontend form-validation libraries, any second database table, soft-delete.

## Risks / Trade-offs

- [Plaintext DB credentials in docker-compose.yml] → Acceptable for a local template scaffold; documented in README as not production-safe. Production deployments should use Docker secrets or an env-file not checked in.
- [Auto-migration on container start can fail if postgres is slow to start] → Mitigated by postgres healthcheck + `depends_on: condition: service_healthy`; Compose will restart the backend container until migration succeeds.
- [`updated_at` must be updated on PUT] → Must be set explicitly in the UPDATE statement (or via a SQLAlchemy `onupdate` default) — PostgreSQL does not auto-update trigger columns without explicit setup.
- [Frontend has no optimistic updates] → Each mutation awaits the API response before re-fetching the list; acceptable latency for a local template.

## Migration Plan

1. Run `docker compose up --build` — postgres starts, backend runs `alembic upgrade head`, uvicorn starts.
2. First `POST /api/users` verifies the table exists and the insert works.
3. To roll back the schema: `docker exec <backend-container> alembic downgrade -1`.
4. To reset all data: `docker compose down -v` removes the `postgres_data` named volume.
