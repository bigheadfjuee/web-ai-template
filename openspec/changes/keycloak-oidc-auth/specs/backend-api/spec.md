## MODIFIED Requirements

### Requirement: FastAPI service managed by uv

The backend SHALL be a FastAPI service located in `backend/`, with dependencies managed by `uv` via `pyproject.toml` and a committed `uv.lock`. The service MUST expose an importable ASGI application at `app.main:app` so it can be started with `uvicorn app.main:app`. The `pyproject.toml` MUST list `PyJWT[cryptography]>=2.4` as a production dependency to support JWKS-based RS256 JWT validation.

#### Scenario: Dependencies install from lockfile

- **WHEN** a developer runs `uv sync --frozen` from `backend/`
- **THEN** the command exits with status `0` and installs the exact versions recorded in `uv.lock` without reaching out to resolve a different set

#### Scenario: Local server starts

- **WHEN** a developer runs `uv run uvicorn app.main:app --port 8000` from `backend/`
- **THEN** uvicorn binds to port `8000` and logs that the FastAPI application started without import errors

#### Scenario: PyJWT with cryptography extras is importable

- **WHEN** `uv run python -c "from jwt import PyJWKClient; print('ok')"` is run from `backend/`
- **THEN** the command prints `ok` and exits with status `0`
