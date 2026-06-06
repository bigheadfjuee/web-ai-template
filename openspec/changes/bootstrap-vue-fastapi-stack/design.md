## Context

`web-ai-template` is the user's reusable starting point for future AI-related web projects. The repository currently contains only empty placeholder files (`frontend/`, `backend/`, `Dockerfile`, `docker-compose.yml`) and a README with a single title line. The proposal calls for a runnable scaffold combining a Vite + Vue 3 SPA, a `uv`-managed FastAPI backend, and an nginx-fronted Docker Compose deployment.

Constraints:

- Tooling is fixed by the requirement: Vite + Vue for the frontend, `uv` + FastAPI for the backend, nginx + Docker Compose for the deployment seam.
- The scaffold must be runnable both as a local dev loop (Vite dev server + `uv run`) and as a single `docker compose up --build` deploy.
- The scaffold should be minimal — enough to prove the wiring end-to-end (`/api/health`), not a real app.

Stakeholders: the repo owner (sole user of the template) and any future fork of this template.

## Goals / Non-Goals

**Goals:**

- A `frontend/` directory that `npm install && npm run dev` and `npm run build` both succeed in, producing a Vite-built SPA that calls `/api/health` and renders the response.
- A `backend/` directory that `uv sync && uv run uvicorn app.main:app --reload` runs locally, serving `GET /api/health` returning `{"status": "ok"}` JSON.
- A `docker compose up --build` from the repo root brings up both services behind nginx on `http://localhost:8080`, with `/` serving the built SPA and `/api/health` reverse-proxied to FastAPI.
- A `README.md` quickstart that documents both flows in under one screen.

**Non-Goals:**

- No auth, database, ORM, or persistence — `/api/health` is the only endpoint.
- No TLS, custom domain, or production secrets handling; the nginx container exposes plain HTTP on host `8080`.
- No CI workflows, image-registry publishing, or Kubernetes manifests.
- No alternative stacks (React, poetry, Caddy) — the choice of Vue / `uv` / nginx is part of the requirement.
- No SSR, hydration, or server-rendered frontend modes — the SPA is statically built and served by nginx.

## Decisions

### Per-service Dockerfiles instead of a single top-level Dockerfile

The repo currently has a top-level `Dockerfile` placeholder. We will instead introduce `frontend/Dockerfile` and `backend/Dockerfile`, and leave the top-level `Dockerfile` either empty-but-tracked or deleted; the implementer SHALL delete it in apply rather than keep a misleading empty file. Rationale: the frontend and backend have completely different base images (`node` + `nginx` vs `python`) and build pipelines; a single multi-target Dockerfile would tangle them and force `docker compose` to use `target:` selectors for no benefit. The cost is two files instead of one, which is negligible.

Alternative considered: a single multi-stage Dockerfile with `frontend-build`, `backend-build`, `frontend-runtime`, `backend-runtime` stages. Rejected because it couples the two services' build caches and obscures which stage belongs to which service when reading the compose file.

### nginx as the only host-exposed service

Only the nginx container publishes a port to the host (`8080:80`). The FastAPI container is reachable only on the internal Compose network as `backend:8000`. Rationale: a single host port matches the proposal's "one runnable stack" intent, avoids CORS in production, and keeps the local-dev CORS surface narrow.

For the local-dev loop (Vite on `5173`, FastAPI on `8000`), CORS will allow `http://localhost:5173` explicitly via FastAPI's `CORSMiddleware`. The Vite dev server will also be configured with a `/api` proxy to `http://localhost:8000` so the dev-time fetch URL matches the production-time URL (`/api/health`).

Alternative considered: publishing both `frontend` and `backend` ports to the host and relying on CORS in production. Rejected because it doubles the host surface and forces every downstream fork to maintain a production CORS allowlist.

### `uv` with `pyproject.toml` + `uv.lock`, no `requirements.txt`

The backend uses `uv` as both the package manager and the lockfile source of truth. The Dockerfile installs deps via `uv sync --frozen --no-dev`. Rationale: `uv` is the requirement; emitting a `requirements.txt` alongside `uv.lock` would invite drift.

Alternative considered: `uv pip compile` to a `requirements.txt` for the Docker stage. Rejected because the `uv sync` path is now well-supported in slim Python images and removes a build step.

### FastAPI app factory in `backend/app/main.py`

The backend exposes `app = create_app()` at module top level (so `uvicorn app.main:app` works), but the FastAPI instance is built inside a `create_app()` function that reads settings from `app/config.py`. Rationale: gives downstream forks a clear extension point (add routers, middleware, lifespan handlers) without rewriting the entry point.

### Vue 3 + TypeScript + `<script setup>` SFCs, no state library

The frontend uses Vue 3, TypeScript, and `<script setup>` single-file components. No Pinia, no Vue Router, no UI library. Rationale: this is a template — every added dependency is one a downstream fork must remove or accept. The HealthCheck component does a single `fetch('/api/health')` on mount.

Alternative considered: scaffolding via `npm create vue@latest` with router + Pinia enabled. Rejected because the resulting boilerplate is larger than what this template needs to demonstrate end-to-end wiring.

### nginx config lives in a top-level `nginx/` directory, mounted into the frontend image

The `nginx/nginx.conf` is copied into the frontend image at build time (not bind-mounted at runtime), so the deployed image is self-contained. The config serves `/usr/share/nginx/html` for `/` and reverse-proxies `/api/` to `http://backend:8000/api/`. Rationale: keeps the runtime image immutable and matches typical container-deploy expectations.

## Implementation Contract

**Observable behaviors (acceptance):**

- From the repo root, `docker compose up --build` exits with both services healthy and `curl -fsS http://localhost:8080/api/health` returns HTTP 200 with body `{"status":"ok"}`.
- From the repo root, `curl -fsS http://localhost:8080/` returns HTTP 200 with the built SPA's `index.html` (containing the Vite-generated `<script type="module">` tag).
- In a browser, `http://localhost:8080/` renders a page that, after the SPA mounts, displays the text "Backend status: ok" (or equivalent) sourced from the `/api/health` response.
- From `backend/`, `uv sync && uv run uvicorn app.main:app --port 8000` starts the server, and `curl -fsS http://localhost:8000/api/health` returns `{"status":"ok"}`.
- From `frontend/`, `npm install && npm run dev` starts the Vite dev server on port `5173`, and the dev-server page shows "Backend status: ok" when the backend is also running on `8000`.
- From `frontend/`, `npm run build` completes without errors and writes static assets under `frontend/dist/`.

**Interfaces / shapes:**

- HTTP: `GET /api/health` → `200 OK`, `Content-Type: application/json`, body `{"status": "ok"}`. No other endpoints in this change.
- Compose services: `frontend` (image built from `frontend/Dockerfile`, listens on container port `80`, publishes `8080:80`), `backend` (image built from `backend/Dockerfile`, listens on container port `8000`, no host publish). Service name `backend` is the DNS name nginx uses.
- nginx routes: `location = /api/health` (and `location /api/`) `proxy_pass http://backend:8000;`; `location /` serves static files with SPA fallback (`try_files $uri /index.html`).
- FastAPI CORS allowlist: only `http://localhost:5173` (the Vite dev server origin). Production traffic is same-origin via nginx and needs no CORS entry.

**Failure modes (intentional):**

- If the backend container is unreachable, nginx returns its default `502 Bad Gateway` for `/api/*`. The SPA SHALL surface the failed health-check as "Backend status: unreachable" rather than crashing.
- If the SPA build step fails, `docker compose up --build` SHALL fail loudly at the frontend image build, not silently produce an empty `dist/`.

**Acceptance verification:**

- Manual: run `docker compose up --build` and execute the two `curl` commands above; both MUST succeed.
- Manual: open `http://localhost:8080/` in a browser and confirm the rendered status string.
- No automated test suite is in scope for this change.

**Scope boundaries:**

- In scope: scaffolding files listed in the proposal's Impact section, the single `/api/health` endpoint, the CORS entry for the Vite dev server, the `README.md` quickstart, and the top-level `.gitignore`.
- Out of scope: any second endpoint, any database wiring, any authentication, any TLS configuration, any GitHub Actions workflow, any pre-commit hook, any storybook or component-library setup.

## Risks / Trade-offs

- [The Vue/Vite/FastAPI/uv versions chosen at scaffold time will drift] → Pin via `package.json` (caret ranges) and `uv.lock` (exact); accept that downstream forks will need to bump.
- [`uv sync --frozen` in the backend image requires `uv.lock` to be committed and in sync with `pyproject.toml`] → The implementer SHALL run `uv lock` before committing and confirm `uv sync --frozen` succeeds in the container build.
- [nginx config bug only surfaces in the Docker path, not in `npm run dev`] → Acceptance MUST include the `docker compose up --build` + `curl` flow, not just the local-dev flow.
- [The `/api` prefix is hardcoded in both FastAPI routes and nginx config] → Documented in the README; downstream forks that want a different prefix must edit both places.
