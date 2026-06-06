## ADDED Requirements

### Requirement: FastAPI service managed by uv

The backend SHALL be a FastAPI service located in `backend/`, with dependencies managed by `uv` via `pyproject.toml` and a committed `uv.lock`. The service MUST expose an importable ASGI application at `app.main:app` so it can be started with `uvicorn app.main:app`.

#### Scenario: Dependencies install from lockfile

- **WHEN** a developer runs `uv sync --frozen` from `backend/`
- **THEN** the command exits with status `0` and installs the exact versions recorded in `uv.lock` without reaching out to resolve a different set

#### Scenario: Local server starts

- **WHEN** a developer runs `uv run uvicorn app.main:app --port 8000` from `backend/`
- **THEN** uvicorn binds to port `8000` and logs that the FastAPI application started without import errors

### Requirement: Health endpoint

The backend SHALL expose `GET /api/health` returning HTTP `200` with `Content-Type: application/json` and body `{"status": "ok"}`.

#### Scenario: Health endpoint returns ok

- **WHEN** a client sends `GET http://localhost:8000/api/health`
- **THEN** the response status is `200`, the `Content-Type` header is `application/json`, and the response body is exactly `{"status":"ok"}` (with no trailing whitespace differences that would break a JSON parse)

### Requirement: App factory and configuration module

The backend SHALL build the FastAPI instance inside a `create_app()` function in `app/main.py`, and SHALL load runtime settings from `app/config.py`. The module-level `app` symbol MUST be the return value of `create_app()` so `uvicorn app.main:app` works without further wiring.

#### Scenario: create_app returns FastAPI instance

- **WHEN** code imports `create_app` from `app.main` and invokes it
- **THEN** the returned object is an instance of `fastapi.FastAPI` with the `/api/health` route registered

### Requirement: CORS allowlist for dev server

The backend SHALL configure CORS to allow requests with origin `http://localhost:5173` so that the Vite dev server can call `/api/*` without browser CORS errors. The allowlist MUST NOT use a wildcard `*` and MUST NOT allow credentials beyond what the dev workflow requires.

#### Scenario: Vite dev origin is allowed

- **WHEN** a browser running the SPA at `http://localhost:5173` performs a fetch to `http://localhost:8000/api/health`
- **THEN** the backend response includes the header `Access-Control-Allow-Origin: http://localhost:5173`

#### Scenario: Unlisted origin is not echoed

- **WHEN** a browser at `http://evil.example` sends a CORS-preflight `OPTIONS` to `/api/health`
- **THEN** the response does not include `Access-Control-Allow-Origin: http://evil.example` and does not use a wildcard `*`
