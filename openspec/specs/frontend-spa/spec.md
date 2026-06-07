## Requirements

### Requirement: Vite + Vue 3 + TypeScript SPA scaffold

The frontend SHALL be a Vite-built single-page application written in Vue 3 with TypeScript single-file components, located in the `frontend/` directory. The scaffold MUST include `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, and a `src/` tree with at least `main.ts` and `App.vue`.

#### Scenario: Local development server starts

- **WHEN** a developer runs `npm install` then `npm run dev` from `frontend/`
- **THEN** Vite starts a dev server listening on `http://localhost:5173` and serves the SPA without TypeScript or Vue-compiler errors

#### Scenario: Production build succeeds

- **WHEN** a developer runs `npm run build` from `frontend/`
- **THEN** Vite emits static assets into `frontend/dist/` including an `index.html` that references the hashed JS bundle as `<script type="module">` and the command exits with status `0`

---
### Requirement: Health-check view wired to backend

The SPA SHALL render a visible health-check indicator that fetches `GET /api/health` on mount, displays the backend status text on success, and displays a non-crashing fallback message on failure.

#### Scenario: Backend reachable

- **WHEN** the SPA mounts and `/api/health` responds `200` with body `{"status":"ok"}`
- **THEN** the page displays the text "Backend status: ok"

#### Scenario: Backend unreachable

- **WHEN** the SPA mounts and `/api/health` returns a network error or non-2xx response
- **THEN** the page displays a fallback such as "Backend status: unreachable" and does not throw an uncaught exception

##### Example: status mapping

| Backend response | Displayed text |
| ---------------- | -------------- |
| `200 {"status":"ok"}` | `Backend status: ok` |
| `200 {"status":"degraded"}` | `Backend status: degraded` |
| network error / 5xx | `Backend status: unreachable` |

---
### Requirement: Dev-server proxy to backend

The Vite dev server SHALL proxy requests with path prefix `/api` to `http://localhost:8000` so that the dev-time fetch URL matches the production-time URL served by nginx.

#### Scenario: Dev fetch reaches FastAPI

- **WHEN** the SPA running under `npm run dev` fetches `/api/health`
- **THEN** the Vite dev server forwards the request to `http://localhost:8000/api/health` and returns the FastAPI response to the browser
