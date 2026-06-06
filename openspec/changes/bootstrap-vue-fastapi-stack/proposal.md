## Why

This repository is a fresh template (`web-ai-template`) with empty placeholder files for `frontend/`, `backend/`, `Dockerfile`, and `docker-compose.yml`, but no actual code or build configuration. We need a runnable, container-deployable starting point that future AI-related web projects can fork — combining a Vite + Vue.js single-page app, a `uv`-managed FastAPI backend, and an nginx-fronted Docker Compose deployment — so each downstream project does not re-derive the same scaffold.

## What Changes

- Scaffold a Vue 3 + TypeScript single-page app under `frontend/` using Vite, with a hello-world view that fetches from the backend `/api/health` endpoint to demonstrate end-to-end wiring.
- Scaffold a FastAPI backend under `backend/` managed by `uv` (via `pyproject.toml` + `uv.lock`), exposing a `/api/health` JSON endpoint and a CORS-aware app factory.
- Provide a multi-stage `Dockerfile` per service: `frontend/Dockerfile` builds the SPA into static assets served by nginx, and `backend/Dockerfile` produces a slim Python image running FastAPI via `uvicorn`.
- Provide a top-level `nginx/` configuration that serves the built SPA on `/` and reverse-proxies `/api/` to the FastAPI service on the internal Compose network.
- Provide a top-level `docker-compose.yml` that wires `frontend` (nginx + SPA), `backend` (FastAPI), and exposes only the nginx container on host port `8080`, so the whole stack is reachable through one port.
- Provide a top-level `README.md` quickstart explaining local dev (`uv run` + `npm run dev`) and container deploy (`docker compose up --build`) flows.

## Non-Goals (optional)

- No production-grade auth, database, or persistence layer — this is a runnable scaffold, not an application.
- No TLS termination, custom domain, or production secrets management; the nginx config exposes plain HTTP on port `8080` and leaves TLS to the deploying environment.
- No CI/CD pipeline, image registry publishing, or Kubernetes manifests in this change.
- No alternative frontend frameworks (React/Svelte), alternative Python package managers (poetry/pip-tools), or alternative reverse proxies (Caddy/Traefik) — `uv`, Vue, and nginx are deliberate choices for this template.

## Capabilities

### New Capabilities

- `frontend-spa`: Vite + Vue 3 + TypeScript single-page app scaffold, including the build pipeline that produces static assets consumable by nginx.
- `backend-api`: FastAPI service managed by `uv`, exposing a `/api/health` endpoint and a CORS-configured app factory ready for extension.
- `container-deploy`: Dockerfiles, nginx reverse-proxy config, and `docker-compose.yml` that compose the frontend and backend into a single runnable stack on host port `8080`.

### Modified Capabilities

(none)

## Impact

- Affected specs: three new capability specs — `frontend-spa`, `backend-api`, `container-deploy`.
- Affected code:
  - New:
    - `frontend/package.json`
    - `frontend/vite.config.ts`
    - `frontend/tsconfig.json`
    - `frontend/index.html`
    - `frontend/src/main.ts`
    - `frontend/src/App.vue`
    - `frontend/src/components/HealthCheck.vue`
    - `frontend/Dockerfile`
    - `frontend/.dockerignore`
    - `backend/pyproject.toml`
    - `backend/uv.lock`
    - `backend/app/__init__.py`
    - `backend/app/main.py`
    - `backend/app/config.py`
    - `backend/Dockerfile`
    - `backend/.dockerignore`
    - `nginx/nginx.conf`
    - `.gitignore`
  - Modified:
    - `Dockerfile` (currently empty — repurposed as a top-level reference or removed in favor of per-service Dockerfiles; see design.md)
    - `docker-compose.yml` (currently empty — filled in with the multi-service stack)
    - `README.md` (expand the title-only file with quickstart instructions)
  - Removed: (none)
