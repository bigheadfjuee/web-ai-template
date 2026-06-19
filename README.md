# Web AI Template

Runnable starting point for AI-related web projects:

- **Frontend** — Vite + Vue 3 + TypeScript SPA under `frontend/`
- **Backend** — FastAPI (managed by `uv`) under `backend/`
- **Deploy** — `docker compose` brings up SQL Server 2019, the backend, and nginx on host ports `80` (HTTP → HTTPS redirect) and `443` (HTTPS, self-signed cert)

## Quickstart — Containers

```bash
docker compose up --build
```

Then verify (the cert is self-signed, so `curl -k` / browser "accept risk" is expected):

- SPA: <https://localhost/>
- Health endpoint: <https://localhost/api/health> → `{"status":"ok"}`
- HTTP redirect: `curl -kI http://localhost/` → `301 Location: https://localhost/`

Only the `nginx` service is published on the host (ports `80` and `443`); the `backend` service is reachable only on the internal Compose network as `backend:8000`, and the `mssql` service uses the internal Compose network as `mssql:1433`. The self-signed certificate is generated inside the nginx image at build time (`CN=localhost`, valid 365 days).

## Quickstart — Local Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/api/health` → `{"status":"ok"}`

## Quickstart — Local Frontend

```bash
cd frontend
pnpm install
pnpm run dev
```

Open <http://localhost:5173/>. The Vite dev server proxies `/api/*` to `http://localhost:8000`, so the backend must also be running for the health-check view to succeed.

## Layout

```
frontend/   Vite + Vue 3 SPA (TypeScript, <script setup> SFCs, no state library)
backend/    FastAPI app managed by uv (pyproject.toml + uv.lock)
nginx/      Dockerfile + reverse-proxy config; multi-stage build that bundles the SPA and terminates TLS on 443
docker-compose.yml
```
