## Context

The stack currently has no authentication layer. The target environment uses Windows Active Directory (AD) as the identity store, and the corporate security policy requires single sign-on via Kerberos (users should not re-enter passwords). Adding Kerberos support directly to FastAPI or Vue would mean embedding GSSAPI/Kerberos bindings, making the app permanently coupled to AD. Keycloak is introduced as a standards-compliant OIDC identity broker: it is the only component that speaks Kerberos, while Vue and FastAPI see only JWT Bearer tokens and standard OIDC flows.

Current state: nginx proxies `/` → Vue SPA (served as static files), `/api/` → FastAPI (port 8000). No authentication exists. All API routes are public.

## Goals / Non-Goals

**Goals:**

- Vue SPA performs OIDC Authorization Code + PKCE login via `keycloak-js`; unauthenticated users are redirected to Keycloak's login page.
- FastAPI validates every protected API request by verifying the Bearer JWT signature against Keycloak's JWKS endpoint; no Kerberos library is imported.
- Keycloak service is added to `docker-compose.yml` and is the sole component aware of AD/Kerberos.
- A realm export JSON (`keycloak/realm-export.json`) documents the Keycloak configuration (LDAP federation, Kerberos authenticator, OIDC client) so the setup is reproducible.
- nginx forwards `/auth/` to Keycloak; the `/` and `/api/` blocks are unchanged.

**Non-Goals:**

- RBAC / fine-grained permissions — all authenticated users are equivalent.
- Migrating existing `users` table rows to Keycloak identities.
- Keycloak HA or clustered deployment.
- Automating AD service-principal or keytab creation (ops responsibility).
- Automating Keycloak realm configuration via IaC tooling.

## Decisions

### Keycloak as the sole Kerberos boundary

**Decision**: Only Keycloak speaks Kerberos. Vue and FastAPI use OIDC/JWT only.

**Rationale**: Kerberos is notoriously difficult to configure in containers and changes across environments (AD forest names, SPNs, keytab rotation). Isolating it to one container means the SPA and API are portable; swapping Keycloak for Okta or Azure AD B2C later requires zero application code changes.

**Alternative considered**: `python-gssapi` in FastAPI — rejected because it requires OS-level Kerberos libraries, makes the backend image AD-specific, and duplicates logic already present in Keycloak.

### Authorization Code + PKCE (no implicit flow, no client secret)

**Decision**: Vue SPA uses Authorization Code + PKCE via `keycloak-js`. The Keycloak client is `publicClient: true`.

**Rationale**: Implicit flow is deprecated (OAuth 2.1). PKCE prevents authorization-code interception without a client secret, which cannot be kept secret in a SPA anyway. `keycloak-js` manages PKCE challenge generation and token refresh transparently.

**Alternative considered**: Device Authorization Grant — rejected, intended for CLI/headless devices, adds unnecessary UX friction in a browser SPA.

### Stateless JWT validation in FastAPI (JWKS, no introspection)

**Decision**: FastAPI fetches Keycloak's JWKS endpoint at startup (and caches the keys), then validates every Bearer JWT locally using `python-jose` or `PyJWT`. No per-request introspection call to Keycloak.

**Rationale**: JWKS validation is ~0 ms (pure crypto). Token introspection adds a network round-trip per request and makes FastAPI dependent on Keycloak availability for every call. The JWT's `exp` claim handles expiry; Keycloak's short access-token lifetime (5 min default) limits the blast radius of a revoked token that slips through.

**Alternative considered**: Per-request introspection (`/protocol/openid-connect/token/introspect`) — rejected due to latency and tight coupling.

### Keycloak hostname via nginx proxy, not direct port exposure

**Decision**: nginx adds `location /auth/` and proxies to the `keycloak` Docker service. Keycloak is not exposed on the host on port 8080/8443.

**Rationale**: Keeps the external surface minimal — only ports 80/443 on nginx. Keycloak's `KC_HOSTNAME` must match the externally visible URL for OIDC metadata and redirect URIs to be consistent.

**Alternative considered**: Expose Keycloak on a dedicated subdomain with its own TLS — valid for production, unnecessary for the template; the single-hostname approach with path prefix is simpler.

### Realm export JSON as the configuration artifact

**Decision**: `keycloak/realm-export.json` is committed to the repo and imported on first Keycloak startup via `--import-realm`. It captures the OIDC client definition, LDAP federation stub, and Kerberos authenticator flow.

**Rationale**: Declarative and version-controlled. Ops staff can adapt the LDAP and Kerberos fields without reading source code.

**Note**: The `keytab` file itself is NOT committed; it is mounted as a Docker secret or volume at deploy time.

## Implementation Contract

### Keycloak service (`docker-compose.yml`)

- A `keycloak` service runs `quay.io/keycloak/keycloak:latest` with `start-dev --import-realm`.
- Environment variables: `KC_HOSTNAME=localhost`, `KC_HTTP_RELATIVE_PATH=/auth`, `KC_HTTP_ENABLED=true`, `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD`.
- Mounts `./keycloak/realm-export.json` into `/opt/keycloak/data/import/realm-export.json`.
- Internal port 8080; not exposed on the host directly.
- `backend` service depends on keycloak being healthy (HTTP `/auth/health/ready`).

### nginx `/auth/` proxy block

- `location /auth/` block added before the `location /` block.
- `proxy_pass http://keycloak:8080;` with standard `proxy_set_header` lines.
- No change to existing `/api/` or `/` blocks.

### Keycloak realm export (`keycloak/realm-export.json`)

- Realm name: `app`.
- OIDC client ID: `vue-spa`, `publicClient: true`, redirect URI: `https://localhost/*`, `pkceCodeChallengeMethod: S256`.
- LDAP User Federation component stub (bindDn, connectionUrl, usersDn as placeholders).
- Kerberos/SPNEGO authentication flow (Browser → Kerberos authenticator → forms fallback).
- Access token lifespan: 300 s (5 min).

### Vue OIDC client (`frontend/src/auth.ts`)

- Exports a singleton `keycloak` instance from `keycloak-js`: `new Keycloak({ url: '/auth', realm: 'app', clientId: 'vue-spa' })`.
- Exports `initKeycloak(): Promise<boolean>` which calls `keycloak.init({ onLoad: 'login-required', pkceMethod: 'S256' })`.
- Exports `getToken(): string` returning `keycloak.token`.
- `frontend/src/main.ts` calls `initKeycloak()` before mounting the Vue app; if init fails, an error screen is shown.
- `frontend/src/api/users.ts` `request()` function adds `Authorization: Bearer <token>` to all requests.

**Acceptance**: After `npm run dev`, navigating to `http://localhost:5173` redirects to `https://localhost/auth/realms/app/protocol/openid-connect/auth`. After login, the app mounts and `GET /api/users` returns 200 with a valid JWT in the `Authorization` header.

### FastAPI JWT validation (`backend/app/auth.py`)

- Module-level: `KEYCLOAK_JWKS_URI` read from environment (`KEYCLOAK_JWKS_URI` env var, default `http://keycloak:8080/auth/realms/app/protocol/openid-connect/certs`).
- `_jwks_client: PyJWKClient` is initialized at module import time using `PyJWKClient(KEYCLOAK_JWKS_URI)` from `PyJWT` >= 2.4.
- `async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict`: fetches the signing key via `_jwks_client.get_signing_key_from_jwt(token)`, decodes and verifies the JWT (`algorithms=["RS256"]`, `options={"verify_aud": False}`), returns the decoded payload dict.
- On failure: raises `HTTPException(status_code=401, detail="Invalid or expired token")`.

**Acceptance**: `curl https://localhost/api/me` without a token returns `{"detail": "Not authenticated"}` (401). With a valid Bearer token it returns the JWT payload as JSON.

### FastAPI `/api/me` endpoint (`backend/app/routers/me.py`)

- `GET /api/me` depends on `get_current_user`; returns the full decoded JWT payload dict as JSON.
- No database query.

### Protected routes

- `/api/users` (all verbs) and `/api/me` require `Depends(get_current_user)`.
- `/api/health` remains public (no auth dependency).

**Scope boundary**: Only the routes in `backend/app/routers/users.py` and `backend/app/routers/me.py` are protected in this change. No other router modifications are in scope.

## Risks / Trade-offs

- [Risk] Keycloak startup is slow (~20-30 s); backend health checks may trip before Keycloak is ready, causing JWKS fetch failures. → Mitigation: `backend` service depends on `keycloak` healthcheck; `PyJWKClient` retries on first request.
- [Risk] Kerberos keytab is environment-specific; the realm export contains a placeholder. → Mitigation: Document the keytab mount path clearly in the realm export and README; the LDAP/Kerberos fields must be filled by the ops team.
- [Risk] JWKS key rotation: if Keycloak rotates keys, the `PyJWKClient` cache becomes stale. → Mitigation: `PyJWKClient` re-fetches when it encounters an unknown `kid`; this is the library's default behavior.
- [Risk] `login-required` onLoad blocks the Vue app entirely if Keycloak is unreachable. → Mitigation: acceptable for an internal corporate app; add a timeout error screen in `main.ts`.
- [Risk] `verify_aud: False` skips audience validation. → Mitigation: add `audience="account"` once the Keycloak client is confirmed; left as False initially to simplify first-run setup.
