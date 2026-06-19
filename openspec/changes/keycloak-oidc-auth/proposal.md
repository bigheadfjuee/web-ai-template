## Why

The application currently has no authentication layer. Adding Kerberos support directly to Vue and FastAPI would create tight coupling to Active Directory, making future migrations to mobile clients, third-party SSO, or MFA expensive code changes. Keycloak acts as a single OIDC broker that absorbs all AD/Kerberos complexity, so the frontend and backend only speak standard OIDC/JWT.

## What Changes

- New `keycloak` service added to `docker-compose.yml` with a dedicated hostname; existing services are unchanged structurally.
- Vue SPA gains an OIDC login/logout flow via `keycloak-js` (Authorization Code + PKCE); unauthenticated routes redirect to Keycloak.
- FastAPI gains JWT Bearer authentication: a startup JWKS fetch from Keycloak, a `get_current_user` dependency that validates every protected route, and a `/api/me` introspection endpoint.
- nginx gains a `location /auth/` proxy block forwarding to Keycloak; existing `/` and `/api/` blocks are unchanged.
- Keycloak is configured (via realm export) with: LDAP User Federation pointing at AD, Kerberos/SPNEGO authenticator with a mounted keytab, and an OIDC public client for the SPA.

## Non-Goals

- This change does NOT add role-based access control (RBAC) or fine-grained permissions; all authenticated users have the same access level.
- This change does NOT migrate or modify existing `users` table data; the AD/Keycloak identity and the local `users` rows remain separate concerns.
- This change does NOT handle Keycloak HA/clustering; a single Keycloak instance is sufficient for the template.
- This change does NOT automate Keycloak realm/client configuration via Terraform or Ansible; the realm export JSON serves as the configuration artifact.
- Kerberos keytab provisioning (creating the service principal in AD) is an ops task outside this change's scope.

## Capabilities

### New Capabilities

- `oidc-auth`: OIDC/JWT authentication layer — Keycloak service, Vue OIDC client flow, FastAPI JWT validation, nginx proxy block for Keycloak, and realm configuration export.

### Modified Capabilities

- `frontend-spa`: SPA gains OIDC login/logout via keycloak-js; unauthenticated users are redirected to Keycloak.
- `backend-api`: FastAPI gains JWKS-based JWT validation and a protected `/api/me` endpoint.
- `container-deploy`: `docker-compose.yml` gains a `keycloak` service; nginx gains a `/auth/` proxy block.

## Impact

- Affected specs: `oidc-auth` (new), `frontend-spa` (delta), `backend-api` (delta), `container-deploy` (delta)
- Affected code:
  - New:
    - `keycloak/realm-export.json`
    - `frontend/src/auth.ts`
    - `frontend/src/components/LoginGuard.vue`
    - `backend/app/auth.py`
    - `backend/app/routers/me.py`
  - Modified:
    - `docker-compose.yml`
    - `nginx/nginx.conf`
    - `frontend/src/main.ts`
    - `frontend/src/App.vue`
    - `frontend/package.json`
    - `backend/pyproject.toml`
    - `backend/uv.lock`
    - `backend/app/main.py`
    - `backend/app/routers/__init__.py`
