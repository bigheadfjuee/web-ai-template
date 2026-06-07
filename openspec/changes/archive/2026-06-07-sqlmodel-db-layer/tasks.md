## 1. Dependencies

- [x] 1.1 Satisfy the SQLAlchemy and Alembic dependencies requirement for SQLModel — add `sqlmodel>=0.0.21` to `backend/pyproject.toml` runtime dependencies, run `uv lock` to update `backend/uv.lock`. Verify by running `uv sync --frozen` (exit 0) then `uv run python -c "from sqlmodel import SQLModel; print('ok')"` (prints `ok`).

## 2. Database layer — db.py and Alembic env

- [x] 2.1 Satisfy the SQLAlchemy 2 async engine and session factory requirement by replacing DeclarativeBase with SQLModel.metadata in db.py — edit `backend/app/db.py` to remove `class Base(DeclarativeBase)` and instead import `from sqlmodel import SQLModel`; export `SQLModel.metadata` so `backend/alembic/env.py` can import it as `target_metadata` (per the "SQLModel table model replaces SQLAlchemy DeclarativeBase model" decision). All other symbols (`engine`, `AsyncSessionLocal`, `get_db`) remain unchanged. Verify by running `uv run python -c "from app.db import AsyncSessionLocal; print('ok')"` (exit 0, no import error).
- [x] 2.2 Update Alembic env.py to use SQLModel.metadata — edit `backend/alembic/env.py` to change the `target_metadata` import from `app.db import Base; target_metadata = Base.metadata` to `from sqlmodel import SQLModel; target_metadata = SQLModel.metadata`, ensuring `import app.models` is still present so all mapped classes register before metadata is read (per the "Alembic migration updated in place" decision). Verify by running `uv run python -c "from alembic.config import Config; c = Config('alembic.ini'); print('ok')"` from `backend/` (exit 0).

## 3. User model — SQLModel table class

- [x] 3.1 Rewrite User as SQLModel table model to satisfy the User model requirement using the dialect-agnostic timestamps with python-side defaults decision — replace the content of `backend/app/models/user.py` with `class User(SQLModel, table=True)` using `Field(default_factory=uuid.uuid4)` for `id`, `Field(max_length=128, unique=True)` for `username` and `Field(max_length=256, unique=True)` for `email`, and `Field(default_factory=lambda: datetime.now(tz=timezone.utc))` for `created_at` and `updated_at`; use `sa_column=Column(sa.Uuid, ...)` and `sa_column=Column(sa.DateTime(timezone=True), ...)` for dialect-agnostic types; remove all imports from `sqlalchemy.dialects.postgresql`. Verify by running (a) `uv run python -c "from app.models.user import User; print(User.__tablename__)"` → prints `users`, and (b) `grep -r "dialects.postgresql" backend/app/` → no output.

## 4. Schemas — SQLModel schema classes

- [x] 4.1 Rewrite schemas to satisfy the Pydantic v2 request and response schemas requirement using SQLModel schema classes — replace `backend/app/schemas/user.py` with `UserBase(SQLModel)`, `UserCreate(UserBase)`, `UserUpdate(SQLModel)` (all fields optional), and `UserPublic(UserBase)` with `id`, `created_at`, `updated_at` and `model_config = ConfigDict(from_attributes=True)` (per the "SQLModel schema classes replace Pydantic BaseModel classes" decision). Verify by running `uv run python -c "from app.schemas.user import UserPublic; print(sorted(UserPublic.model_fields.keys()))"` → prints `['created_at', 'email', 'id', 'updated_at', 'username']`.

## 5. Router — rename UserResponse to UserPublic

- [x] 5.1 Update the CRUD router at /api/users to satisfy the CRUD router at /api/users requirement — edit `backend/app/routers/users.py` to replace all occurrences of `UserResponse` with `UserPublic` in imports and `response_model=` arguments; no endpoint logic changes. Verify by running (a) `grep "UserResponse" backend/app/routers/users.py` → no output, and (b) `uv run python -c "from app.routers.users import router; print(len(router.routes))"` → prints `5`.

## 6. Alembic migration — dialect-agnostic DDL

- [x] 6.1 Apply the alembic migration updated in place (no new revision) and dialect-agnostic UUID primary key decisions to satisfy the Alembic migration for users table requirement — edit `backend/alembic/versions/0001_create_users_table.py` to replace the raw SQL `CREATE TABLE` string and `CREATE EXTENSION pgcrypto` with SQLAlchemy op calls: `op.create_table("users", sa.Column("id", sa.Uuid, primary_key=True), sa.Column("username", sa.String(128), nullable=False, unique=True), sa.Column("email", sa.String(256), nullable=False, unique=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))` and `downgrade()` calls `op.drop_table("users")`; the revision ID stays `0001`. Verify by running `uv run python -c "import importlib.util; spec=importlib.util.spec_from_file_location('m','alembic/versions/0001_create_users_table.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print(m.revision)"` from `backend/` → prints `0001` with no error; also run `grep "gen_random_uuid" backend/alembic/versions/0001_create_users_table.py` → no output.

## 7. End-to-end verification

- [x] 7.1 Verify no PostgreSQL dialect imports remain — run `grep -r "dialects.postgresql" backend/app/` and `grep -r "gen_random_uuid" backend/` from the repo root. Both MUST return no output (exit non-zero or zero matches). If any match is found, fix the file before marking this task done.
- [x] 7.2 Full stack rebuild and CRUD curl sequence — run `docker compose down -v && docker compose up --build` from the repo root; wait for the backend to log `Running upgrade -> 0001` then uvicorn ready; execute the seven-step curl sequence: (a) `curl -fsSk https://localhost/api/users` → `200 []`, (b) POST a user → `201` with UUID id, (c) GET by id → `200`, (d) PUT email → `200` with `updated_at >= created_at`, (e) DELETE → `204`, (f) GET deleted → `404`, (g) POST duplicate → `409`. All seven MUST pass.
