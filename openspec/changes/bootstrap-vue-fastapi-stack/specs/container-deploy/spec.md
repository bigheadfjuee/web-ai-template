## ADDED Requirements

### Requirement: Per-service Dockerfiles

The repository SHALL provide `frontend/Dockerfile` and `backend/Dockerfile`. The frontend Dockerfile MUST be multi-stage: a Node-based stage that runs `npm ci` and `npm run build`, followed by an `nginx`-based stage that copies `frontend/dist/` into the nginx web root and copies `nginx/nginx.conf` into the nginx config path. The backend Dockerfile MUST install dependencies via `uv sync --frozen --no-dev` and run `uvicorn app.main:app --host 0.0.0.0 --port 8000` as its default command.

#### Scenario: Frontend image builds

- **WHEN** `docker build -f frontend/Dockerfile frontend/` is run from the repo root
- **THEN** the build completes successfully and the resulting image's `/usr/share/nginx/html/index.html` exists and references the Vite-built hashed JS bundle

#### Scenario: Backend image builds

- **WHEN** `docker build -f backend/Dockerfile backend/` is run from the repo root
- **THEN** the build completes successfully and the resulting image's default command starts uvicorn serving `app.main:app` on port `8000`

### Requirement: nginx reverse proxy configuration

The repository SHALL provide an `nginx/nginx.conf` that is baked into the frontend image at build time (not bind-mounted at runtime). The config MUST serve static SPA assets from the nginx web root at `/` with an SPA fallback (`try_files $uri /index.html`) and MUST reverse-proxy requests under `/api/` to `http://backend:8000` using the Compose-network DNS name `backend`.

#### Scenario: Static SPA served at root

- **WHEN** a client requests `http://localhost:8080/`
- **THEN** nginx returns HTTP `200` with the built SPA's `index.html`

#### Scenario: SPA fallback for client-side routes

- **WHEN** a client requests `http://localhost:8080/some/unknown/route`
- **THEN** nginx returns HTTP `200` with `index.html` rather than `404`, so the SPA can handle the route

#### Scenario: API requests proxied to backend

- **WHEN** a client requests `http://localhost:8080/api/health`
- **THEN** nginx forwards the request to `http://backend:8000/api/health` over the internal Compose network and returns the FastAPI response to the client

### Requirement: docker-compose stack with single host port

The repository SHALL provide a top-level `docker-compose.yml` defining two services: `frontend` built from `frontend/Dockerfile` and `backend` built from `backend/Dockerfile`. Only the `frontend` service MUST publish a host port, mapping host `8080` to container `80`. The `backend` service MUST NOT publish a host port; it MUST be reachable only on the internal Compose network as the DNS name `backend` on port `8000`.

#### Scenario: Stack comes up and health passes end-to-end

- **WHEN** a developer runs `docker compose up --build` from the repo root and waits for both services to report ready
- **THEN** `curl -fsS http://localhost:8080/api/health` returns HTTP `200` with body `{"status":"ok"}` and `curl -fsS http://localhost:8080/` returns the SPA's `index.html`

#### Scenario: Backend not exposed to host

- **WHEN** the stack is running and a client attempts `curl -fsS http://localhost:8000/api/health`
- **THEN** the connection is refused or times out, because the `backend` service does not publish port `8000` to the host

### Requirement: Repo-root quickstart documentation

The repository SHALL include a `README.md` at the repo root that documents both the local-dev flow (one block for `frontend/`, one for `backend/`) and the container-deploy flow (`docker compose up --build` plus the verification `curl` commands). The README MUST name the host port (`8080`) and the health URL (`/api/health`) explicitly.

#### Scenario: README covers both flows

- **WHEN** a reader opens `README.md` after this change ships
- **THEN** the file contains a runnable `docker compose up --build` block, a runnable local-dev block for the backend (`uv sync` + `uv run uvicorn`), a runnable local-dev block for the frontend (`npm install` + `npm run dev`), and an explicit mention of `http://localhost:8080/api/health` as the verification URL
