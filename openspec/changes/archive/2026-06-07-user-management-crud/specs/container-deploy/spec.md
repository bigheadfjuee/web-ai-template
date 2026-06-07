## ADDED Requirements

### Requirement: PostgreSQL service in docker-compose.yml

The `docker-compose.yml` SHALL define a `postgres` service using `postgres:16-alpine` with environment variables `POSTGRES_USER=appuser`, `POSTGRES_PASSWORD=apppassword`, `POSTGRES_DB=appdb`, a named volume `postgres_data` mounted at `/var/lib/postgresql/data`, and a healthcheck that runs `pg_isready -U appuser -d appdb` every 5 seconds with a 5-second timeout and 5 retries.

#### Scenario: Postgres healthcheck passes

- **WHEN** `docker compose up` is run and postgres has started
- **THEN** `docker compose ps` shows the `postgres` container status as `healthy` within 60 seconds

### Requirement: Backend service depends on postgres health

The `backend` service in `docker-compose.yml` SHALL declare `depends_on` with `condition: service_healthy` pointing to the `postgres` service. The backend service SHALL set the `DATABASE_URL` environment variable to `postgresql+asyncpg://appuser:apppassword@postgres:5432/appdb`.

#### Scenario: Backend starts only after postgres is healthy

- **WHEN** `docker compose up` is run from a clean state
- **THEN** the backend container does not emit uvicorn startup log lines until the postgres healthcheck passes

### Requirement: Named volume postgres_data declared in Compose

The top-level `volumes:` section of `docker-compose.yml` SHALL declare `postgres_data:` so Docker manages the volume lifecycle. The volume SHALL persist data across `docker compose down` (without `-v`).

#### Scenario: postgres_data volume declared

- **WHEN** `docker compose config` is inspected
- **THEN** `postgres_data` appears in the `volumes:` section at the top level

### Requirement: Backend Dockerfile uses migration-then-start CMD

The `backend/Dockerfile` `CMD` SHALL be updated to run `alembic upgrade head` before launching uvicorn, using the form `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"`. The `WORKDIR` in the Dockerfile SHALL be `/app` so that `alembic.ini` at `/app/alembic.ini` is found by Alembic automatically.

#### Scenario: Migration runs before API is reachable

- **WHEN** the backend container starts from a fresh database
- **THEN** `alembic upgrade head` exits with status `0` and the `users` table exists before the first HTTP request is served
