## MODIFIED Requirements

### Requirement: Vite + Vue 3 + TypeScript SPA scaffold

The frontend SHALL be a Vite-built single-page application written in Vue 3 with TypeScript single-file components, located in the `frontend/` directory. The scaffold MUST include `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, and a `src/` tree with at least `main.ts`, `App.vue`, and `auth.ts`. The `package.json` MUST list `keycloak-js` as a production dependency. The `main.ts` entry point MUST call `initKeycloak()` from `frontend/src/auth.ts` before mounting the Vue application; if `initKeycloak()` resolves to `false` or rejects, an error message SHALL be displayed instead of mounting the app.

#### Scenario: Local development server starts

- **WHEN** a developer runs `npm install` then `npm run dev` from `frontend/`
- **THEN** Vite starts a dev server listening on `http://localhost:5173` and serves the SPA without TypeScript or Vue-compiler errors

#### Scenario: Production build succeeds

- **WHEN** a developer runs `npm run build` from `frontend/`
- **THEN** Vite emits static assets into `frontend/dist/` including an `index.html` that references the hashed JS bundle as `<script type="module">` and the command exits with status `0`

#### Scenario: keycloak-js is present in the production bundle

- **WHEN** `npm run build` completes
- **THEN** the `frontend/dist/assets/` directory contains a JavaScript chunk that includes keycloak-js code (verifiable by `grep -r "Keycloak" frontend/dist/` returning at least one match)
