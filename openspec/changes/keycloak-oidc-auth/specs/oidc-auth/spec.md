## ADDED Requirements

### Requirement: Keycloak service in Compose

The `docker-compose.yml` SHALL include a `keycloak` service using `quay.io/keycloak/keycloak:latest` configured with `start-dev --import-realm`. The service SHALL set `KC_HTTP_RELATIVE_PATH=/auth` and `KC_HOSTNAME=localhost` so that OIDC metadata URLs are rooted at `https://localhost/auth/`. The service SHALL mount `./keycloak/realm-export.json` into `/opt/keycloak/data/import/realm-export.json`. The `backend` service SHALL declare `depends_on: keycloak: condition: service_healthy`. The `keycloak` service SHALL NOT expose its port directly on the host.

#### Scenario: Keycloak OIDC discovery endpoint is reachable through nginx

- **WHEN** the full stack is running and a client sends `GET https://localhost/auth/realms/app/.well-known/openid-configuration`
- **THEN** the response is HTTP 200 with a JSON body containing `"issuer": "https://localhost/auth/realms/app"` and `"jwks_uri"` pointing to `https://localhost/auth/realms/app/protocol/openid-connect/certs`

#### Scenario: Keycloak starts before the backend

- **WHEN** `docker compose up` is run on a clean environment
- **THEN** the `keycloak` healthcheck passes before the `backend` container transitions to `running` state

---

### Requirement: Realm export configuration artifact

The repository SHALL include `keycloak/realm-export.json` committing the Keycloak realm configuration. The export MUST define: realm name `app`; an OIDC public client with ID `vue-spa`, `publicClient: true`, redirect URI `https://localhost/*`, and `pkceCodeChallengeMethod: S256`; an LDAP User Federation component with placeholder `connectionUrl`, `bindDn`, `usersDn` fields; a Kerberos/SPNEGO browser authentication flow that falls back to username/password forms; and an access token lifespan of 300 seconds.

#### Scenario: Realm is imported on first startup

- **WHEN** the `keycloak` container starts for the first time against an empty data volume
- **THEN** the realm `app` exists in Keycloak admin console and the `vue-spa` client is visible with `publicClient: true`

#### Scenario: Keytab is not committed to the repository

- **WHEN** `git ls-files keycloak/` is run from the repo root
- **THEN** no file with extension `.keytab` appears in the output

---

### Requirement: nginx proxy block for Keycloak

nginx SHALL forward all requests matching `location /auth/` to `http://keycloak:8080` via `proxy_pass`. The block SHALL set `proxy_set_header Host`, `X-Real-IP`, `X-Forwarded-For`, and `X-Forwarded-Proto` identically to the `/api/` block. The existing `/api/` and `/` location blocks SHALL remain unchanged.

#### Scenario: nginx routes /auth/ to Keycloak

- **WHEN** the stack is running and a request is sent to `GET https://localhost/auth/realms/app/.well-known/openid-configuration`
- **THEN** nginx proxies the request to the `keycloak` service and returns the Keycloak response with HTTP 200

---

### Requirement: Vue OIDC client module

The frontend SHALL include `frontend/src/auth.ts` that exports a singleton `keycloak` instance constructed as `new Keycloak({ url: '/auth', realm: 'app', clientId: 'vue-spa' })` from the `keycloak-js` package. The module SHALL export `initKeycloak(): Promise<boolean>` which calls `keycloak.init({ onLoad: 'login-required', pkceMethod: 'S256' })`. The module SHALL export `getToken(): string` returning `keycloak.token`.

#### Scenario: Unauthenticated user is redirected to Keycloak

- **WHEN** a user navigates to the SPA root without a valid Keycloak session
- **THEN** `initKeycloak()` triggers a browser redirect to `https://localhost/auth/realms/app/protocol/openid-connect/auth` with `response_type=code` and a PKCE `code_challenge` parameter

#### Scenario: Vue app mounts only after successful authentication

- **WHEN** `initKeycloak()` resolves to `true`
- **THEN** `createApp(App).mount('#app')` is called and the Vue component tree renders

#### Scenario: API requests carry a Bearer token

- **WHEN** the `request()` helper in `frontend/src/api/users.ts` is called after the user is authenticated
- **THEN** the outgoing `fetch` request includes an `Authorization: Bearer <token>` header where `<token>` is the value returned by `getToken()`

---

### Requirement: FastAPI JWKS-based JWT validation

The backend SHALL include `backend/app/auth.py` that reads `KEYCLOAK_JWKS_URI` from the environment (default `http://keycloak:8080/auth/realms/app/protocol/openid-connect/certs`) and initializes a `PyJWKClient` at module import time. The module SHALL expose `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)` and an async function `get_current_user(token: str = Depends(oauth2_scheme)) -> dict` that fetches the signing key via `_jwks_client.get_signing_key_from_jwt(token)`, decodes the JWT with `algorithm="RS256"`, and returns the payload dict. On any verification failure the function SHALL raise `HTTPException(status_code=401)`.

#### Scenario: Request with valid Bearer JWT is accepted

- **WHEN** `GET https://localhost/api/me` is called with `Authorization: Bearer <valid-jwt>` where the JWT is issued by Keycloak realm `app`
- **THEN** FastAPI returns HTTP 200 and a JSON body containing at minimum the `sub` and `preferred_username` claims from the token

#### Scenario: Request without a Bearer token is rejected

- **WHEN** `GET https://localhost/api/me` is called with no `Authorization` header
- **THEN** FastAPI returns HTTP 401

#### Scenario: Request with an expired or tampered JWT is rejected

- **WHEN** `GET https://localhost/api/me` is called with a JWT whose `exp` is in the past or whose signature has been altered
- **THEN** FastAPI returns HTTP 401

---

### Requirement: Protected /api/me endpoint

The backend SHALL include `backend/app/routers/me.py` that registers `GET /api/me` on the FastAPI app. The endpoint SHALL depend on `get_current_user` from `backend/app/auth.py` and SHALL return the full decoded JWT payload dict as a JSON response. The endpoint SHALL NOT perform any database query.

#### Scenario: /api/me returns JWT payload for authenticated user

- **WHEN** `GET https://localhost/api/me` is called with a valid Bearer JWT
- **THEN** the response body is the JSON-serialized decoded JWT payload including `sub`, `preferred_username`, and `email` claims (when present in the token)

---

### Requirement: /api/users routes protected by JWT

All routes registered under `/api/users` SHALL depend on `get_current_user` from `backend/app/auth.py`. The `/api/health` endpoint SHALL remain public (no auth dependency).

#### Scenario: Unauthenticated request to /api/users is rejected

- **WHEN** `GET https://localhost/api/users` is called with no `Authorization` header
- **THEN** FastAPI returns HTTP 401

#### Scenario: /api/health remains publicly accessible

- **WHEN** `GET https://localhost/api/health` is called with no `Authorization` header
- **THEN** FastAPI returns HTTP 200 `{"status": "ok"}`
