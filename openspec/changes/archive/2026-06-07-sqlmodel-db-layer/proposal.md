## Summary

Replace the current split SQLAlchemy ORM model + Pydantic schema approach with SQLModel, and remove all PostgreSQL-dialect-specific SQL so the database layer can be pointed at MSSQL with a driver swap only.

## Motivation

The current backend uses:
- `sqlalchemy.dialects.postgresql.UUID` — PostgreSQL-only column type
- `server_default=text("gen_random_uuid()")` — PostgreSQL built-in function
- `server_default=text("now()")` — while valid on MSSQL, the overall column type `TIMESTAMPTZ` is PostgreSQL-only
- Separate `app/models/user.py` (SQLAlchemy ORM) and `app/schemas/user.py` (Pydantic) — two classes describing the same entity

SQLModel unifies ORM model and Pydantic schema into a single `SQLModel` class, eliminating the duplication. Replacing dialect-specific column defaults with database-agnostic SQLAlchemy alternatives (`default=uuid.uuid4` for client-side UUID generation, `DateTime(timezone=True)` with Python-side defaults) makes the schema portable.

## Proposed Solution

1. Add `sqlmodel` to `backend/pyproject.toml`; remove direct `sqlalchemy` ORM imports from model/schema files (SQLModel re-exports the SQLAlchemy async engine and session).
2. Rewrite `backend/app/models/user.py` as a `SQLModel` table model (`class User(SQLModel, table=True)`). Use `Field(default_factory=uuid.uuid4)` for the UUID PK and `Field(default_factory=datetime.utcnow)` for timestamps — no `server_default`.
3. Replace the separate `UserCreate`, `UserUpdate`, `UserResponse` Pydantic classes in `backend/app/schemas/user.py` with SQLModel-native schema models (`class UserCreate(SQLModel)`, `class UserUpdate(SQLModel)`, `class UserPublic(SQLModel)`) that share field definitions with the table model via inheritance.
4. Update `backend/app/db.py` to derive the async engine and session from `sqlmodel.ext.asyncio.session.AsyncSession` (or keep `sqlalchemy.ext.asyncio` directly — SQLModel is compatible with both).
5. Update the Alembic migration `0001_create_users_table` to use dialect-agnostic DDL: `sa.Column("id", sa.Uuid, primary_key=True)` with no `server_default`; `sa.Column("created_at", sa.DateTime(timezone=True))` with no `server_default`. UUID and timestamp values are generated client-side by SQLModel defaults.
6. Update `backend/app/routers/users.py` to use the new schema class names (`UserPublic` instead of `UserResponse`).

## Non-Goals

- No actual MSSQL driver (pyodbc / aioodbc) is added; MSSQL connectivity is a deployment-time concern.
- No MSSQL Compose service or MSSQL CI test is added.
- No behavioral changes to the REST API — endpoints, response shapes, and status codes remain identical.
- No changes to the frontend (`frontend/src/api/users.ts`, `UsersView.vue`).
- No changes to nginx, docker-compose, or the postgres Compose service.
- No new migrations — the existing `0001` migration is updated in place (the database has not been deployed to production; the volume can be recreated).

## Alternatives Considered

- Keep SQLAlchemy ORM + Pydantic, only fix dialect-specific columns. Rejected: does not address the model/schema duplication that SQLModel eliminates, misses the stated goal of adopting SQLModel.
- Use SQLModel's `create_all` instead of Alembic. Rejected: Alembic provides reversible migrations and should be retained for production use.

## Impact

- Affected specs: modified — `backend-api` (new SQLModel dep), `postgres-db` (dialect-agnostic DDL), `user-api` (SQLModel table + schema classes, renamed `UserPublic`)
- Affected code:
  - Modified:
    - `backend/pyproject.toml`
    - `backend/uv.lock`
    - `backend/app/db.py`
    - `backend/app/models/user.py`
    - `backend/app/schemas/user.py`
    - `backend/app/routers/users.py`
    - `backend/alembic/versions/0001_create_users_table.py`
  - New: (none)
  - Removed: (none)
