## MODIFIED Requirements

### Requirement: Alembic migration for users table

The Alembic migration `0001_create_users_table` SHALL be updated so that its `upgrade()` function uses dialect-agnostic SQLAlchemy types only: `sa.Uuid` for the `id` column (no `server_default`), `sa.String(128)` for `username`, `sa.String(256)` for `email`, and `sa.DateTime(timezone=True)` for `created_at` and `updated_at` (no `server_default`). The `pgcrypto` extension creation and `gen_random_uuid()` function reference MUST be removed. The `downgrade()` function remains `DROP TABLE IF EXISTS users`. Running `alembic upgrade head` on a fresh database MUST succeed and produce a `users` table; running `alembic downgrade -1` MUST drop it.

#### Scenario: Migration applies without PostgreSQL extensions

- **WHEN** `alembic upgrade head` is run against a fresh PostgreSQL database without the `pgcrypto` extension pre-installed
- **THEN** the migration exits with status `0` and the `users` table is created with columns `id`, `username`, `email`, `created_at`, `updated_at`

#### Scenario: Migration is reversible

- **WHEN** `alembic downgrade -1` is run after a successful `alembic upgrade head`
- **THEN** the `users` table is dropped and `alembic_version` records no applied revisions

### Requirement: SQLAlchemy 2 async engine and session factory

The `backend/app/db.py` module SHALL replace `class Base(DeclarativeBase)` with `from sqlmodel import SQLModel` and expose `SQLModel.metadata` as the authoritative metadata object used by Alembic's `env.py` `target_metadata`. The async engine, `AsyncSessionLocal`, and `get_db` dependency SHALL remain functionally identical — only the metadata source changes.

#### Scenario: SQLModel.metadata used by Alembic env

- **WHEN** `backend/alembic/env.py` imports `target_metadata` from `app.db`
- **THEN** `target_metadata` is `SQLModel.metadata` and contains the `users` table definition after `app.models` is imported
