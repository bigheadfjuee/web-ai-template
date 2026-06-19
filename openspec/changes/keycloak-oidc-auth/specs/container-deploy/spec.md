## MODIFIED Requirements

### Requirement: Per-service Dockerfiles

The repository SHALL provide a `nginx/Dockerfile` (multi-stage: Node builder + nginx runtime) and `backend/Dockerfile`. The nginx Dockerfile MUST produce a stage that copies `nginx/nginx.conf` — which MUST include `location /auth/` proxy rules forwarding to the `keycloak` service — into the nginx config path. The backend Dockerfile MUST install dependencies via `uv sync --frozen --no-dev` and run `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` as its default command.

#### Scenario: Frontend image builds

- **WHEN** `docker build -f nginx/Dockerfile .` is run from the repo root
- **THEN** the build completes successfully and the resulting image's `/usr/share/nginx/html/index.html` exists and references the Vite-built hashed JS bundle

#### Scenario: Backend image builds

- **WHEN** `docker build -f backend/Dockerfile backend/` is run from the repo root
- **THEN** the build completes successfully and the resulting image's default command starts uvicorn serving `app.main:app` on port `8000`

## ADDED Requirements

### Requirement: Keycloak configuration directory

The repository SHALL include a `keycloak/` directory at the repo root containing at minimum `realm-export.json`. This file SHALL be the sole source of truth for the Keycloak realm, OIDC client, LDAP federation stub, and Kerberos authenticator flow configuration. No `.keytab` files SHALL be committed to the repository.

#### Scenario: keycloak/ directory exists and contains realm-export.json

- **WHEN** `ls keycloak/` is run from the repo root
- **THEN** `realm-export.json` appears in the output

#### Scenario: No keytab files are tracked by git

- **WHEN** `git ls-files keycloak/` is run from the repo root
- **THEN** no file with extension `.keytab` appears in the output and the command exits with status `0`
