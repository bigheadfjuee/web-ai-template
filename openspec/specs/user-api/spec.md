# user-api Specification

## Purpose

TBD - created by archiving change 'user-management-crud'. Update Purpose after archive.

## Requirements

### Requirement: User model

The backend SHALL define a SQLAlchemy `User` ORM model in `backend/app/models/user.py` mapping to the `users` table with columns `id`, `username`, `email`, `created_at`, and `updated_at` matching the Alembic migration schema.

#### Scenario: User model is importable and maps to the users table

- **WHEN** code imports `User` from `app.models.user`
- **THEN** `User.__tablename__` is `"users"` and the model has attributes `id`, `username`, `email`, `created_at`, `updated_at`


<!-- @trace
source: user-management-crud
updated: 2026-06-07
code:
  - backend/app/routers/users.py
  - frontend/src/App.vue
  - backend/app/config.py
  - backend/app/main.py
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/alembic.ini
  - backend/app/schemas/user.py
  - backend/alembic/script.py.mako
  - backend/app/models/user.py
  - backend/app/models/__init__.py
  - backend/alembic/README
  - docker-compose.yml
  - frontend/src/views/UsersView.vue
  - backend/app/schemas/__init__.py
  - frontend/src/api/users.ts
  - backend/alembic/versions/0001_create_users_table.py
  - backend/app/routers/__init__.py
  - backend/uv.lock
  - backend/Dockerfile
  - backend/pyproject.toml
-->

---
### Requirement: Pydantic v2 request and response schemas

The backend SHALL define Pydantic v2 schemas in `backend/app/schemas/user.py`:
- `UserCreate` with required fields `username: str` and `email: EmailStr`
- `UserUpdate` with optional fields `username: str | None = None` and `email: EmailStr | None = None`
- `UserResponse` with fields `id: UUID`, `username: str`, `email: str`, `created_at: datetime`, `updated_at: datetime`; `UserResponse` SHALL be configured with `model_config = ConfigDict(from_attributes=True)` for ORM serialization.

#### Scenario: UserResponse serializes from ORM instance

- **WHEN** a `User` ORM instance is passed to `UserResponse.model_validate(user)`
- **THEN** the result is a `UserResponse` with all five fields populated from the ORM object's attributes


<!-- @trace
source: user-management-crud
updated: 2026-06-07
code:
  - backend/app/routers/users.py
  - frontend/src/App.vue
  - backend/app/config.py
  - backend/app/main.py
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/alembic.ini
  - backend/app/schemas/user.py
  - backend/alembic/script.py.mako
  - backend/app/models/user.py
  - backend/app/models/__init__.py
  - backend/alembic/README
  - docker-compose.yml
  - frontend/src/views/UsersView.vue
  - backend/app/schemas/__init__.py
  - frontend/src/api/users.ts
  - backend/alembic/versions/0001_create_users_table.py
  - backend/app/routers/__init__.py
  - backend/uv.lock
  - backend/Dockerfile
  - backend/pyproject.toml
-->

---
### Requirement: CRUD router at /api/users

The backend SHALL expose a FastAPI router registered at prefix `/api/users` implementing five endpoints:
- `POST /api/users` — creates a user; returns `201 UserResponse`
- `GET /api/users?skip=0&limit=100` — lists users paginated; returns `200 list[UserResponse]`
- `GET /api/users/{id}` — retrieves a single user by UUID; returns `200 UserResponse` or `404 {"detail":"User not found"}`
- `PUT /api/users/{id}` — partially updates username and/or email; returns `200 UserResponse`, `404`, or `409 {"detail":"Username or email already exists"}`
- `DELETE /api/users/{id}` — hard-deletes user; returns `204` with no body, or `404`

#### Scenario: Create user succeeds

- **WHEN** `POST /api/users` is called with `{"username":"alice","email":"alice@example.com"}`
- **THEN** the response status is `201`, the body contains a `UserResponse` with `id` as a UUID string, `username` as `"alice"`, `email` as `"alice@example.com"`, and non-null `created_at` and `updated_at`

#### Scenario: Duplicate username returns 409

- **WHEN** `POST /api/users` is called twice with the same `username`
- **THEN** the first call returns `201` and the second returns `409` with body `{"detail":"Username or email already exists"}`

#### Scenario: List users with pagination

- **WHEN** `GET /api/users?skip=0&limit=2` is called with three users in the database
- **THEN** the response status is `200` and the body is a JSON array of exactly two `UserResponse` objects

##### Example: pagination boundary

| skip | limit | users in DB | expected count in response |
| ---- | ----- | ----------- | -------------------------- |
| 0    | 2     | 3           | 2                          |
| 2    | 2     | 3           | 1                          |
| 3    | 2     | 3           | 0                          |

#### Scenario: Get non-existent user returns 404

- **WHEN** `GET /api/users/<random-uuid>` is called with a UUID that does not exist in the database
- **THEN** the response status is `404` and the body is `{"detail":"User not found"}`

#### Scenario: Update email only

- **WHEN** `PUT /api/users/{id}` is called with body `{"email":"new@example.com"}` and `username` omitted
- **THEN** the response status is `200`, the `email` field is updated to `"new@example.com"`, the `username` is unchanged, and `updated_at` is greater than or equal to `created_at`

#### Scenario: Delete user

- **WHEN** `DELETE /api/users/{id}` is called for an existing user
- **THEN** the response status is `204` with no body; a subsequent `GET /api/users/{id}` returns `404`


<!-- @trace
source: user-management-crud
updated: 2026-06-07
code:
  - backend/app/routers/users.py
  - frontend/src/App.vue
  - backend/app/config.py
  - backend/app/main.py
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/alembic.ini
  - backend/app/schemas/user.py
  - backend/alembic/script.py.mako
  - backend/app/models/user.py
  - backend/app/models/__init__.py
  - backend/alembic/README
  - docker-compose.yml
  - frontend/src/views/UsersView.vue
  - backend/app/schemas/__init__.py
  - frontend/src/api/users.ts
  - backend/alembic/versions/0001_create_users_table.py
  - backend/app/routers/__init__.py
  - backend/uv.lock
  - backend/Dockerfile
  - backend/pyproject.toml
-->

---
### Requirement: IntegrityError mapped to 409

The backend SHALL catch `sqlalchemy.exc.IntegrityError` raised by unique constraint violations on `username` or `email` and return `409` with body `{"detail":"Username or email already exists"}`. The error SHALL NOT propagate as a `500`.

#### Scenario: IntegrityError on email update returns 409

- **WHEN** `PUT /api/users/{id}` is called with an `email` value already used by another user
- **THEN** the response status is `409` and the body is `{"detail":"Username or email already exists"}`

<!-- @trace
source: user-management-crud
updated: 2026-06-07
code:
  - backend/app/routers/users.py
  - frontend/src/App.vue
  - backend/app/config.py
  - backend/app/main.py
  - backend/alembic/env.py
  - backend/app/db.py
  - backend/alembic.ini
  - backend/app/schemas/user.py
  - backend/alembic/script.py.mako
  - backend/app/models/user.py
  - backend/app/models/__init__.py
  - backend/alembic/README
  - docker-compose.yml
  - frontend/src/views/UsersView.vue
  - backend/app/schemas/__init__.py
  - frontend/src/api/users.ts
  - backend/alembic/versions/0001_create_users_table.py
  - backend/app/routers/__init__.py
  - backend/uv.lock
  - backend/Dockerfile
  - backend/pyproject.toml
-->