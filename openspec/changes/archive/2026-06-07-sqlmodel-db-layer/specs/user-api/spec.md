## MODIFIED Requirements

### Requirement: User model

The `User` class in `backend/app/models/user.py` SHALL be rewritten as `class User(SQLModel, table=True)` with `__tablename__ = "users"`. Field definitions MUST use `sqlmodel.Field` and `sqlalchemy` generic types only:

- `id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(sa.Uuid, primary_key=True, default=uuid.uuid4))`
- `username: str = Field(max_length=128, unique=True, nullable=False, index=False)`
- `email: str = Field(max_length=256, unique=True, nullable=False)`
- `created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), sa_column=Column(sa.DateTime(timezone=True), nullable=False))`
- `updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), sa_column=Column(sa.DateTime(timezone=True), nullable=False))`

The import `from sqlalchemy.dialects.postgresql import UUID` MUST NOT appear in `backend/app/models/user.py` or any other file under `backend/app/`. The string `gen_random_uuid` MUST NOT appear anywhere in `backend/`.

#### Scenario: User model has no PostgreSQL-dialect imports

- **WHEN** `grep -r "dialects.postgresql" backend/app/` is run from the repo root
- **THEN** the command returns no output (exit status 1 or zero matches)

#### Scenario: User model is importable and maps to users table

- **WHEN** `uv run python -c "from app.models.user import User; print(User.__tablename__)"` is run from `backend/`
- **THEN** the output is `users` and no import error occurs

### Requirement: Pydantic v2 request and response schemas

The `backend/app/schemas/user.py` SHALL be rewritten using SQLModel classes:

- `class UserBase(SQLModel)` — non-table base with `username: str` and `email: EmailStr`
- `class UserCreate(UserBase)` — no additional fields; used as POST request body
- `class UserUpdate(SQLModel)` — `username: str | None = None` and `email: EmailStr | None = None`; all fields optional (does NOT inherit `UserBase`)
- `class UserPublic(UserBase)` — adds `id: uuid.UUID`, `created_at: datetime`, `updated_at: datetime`; configured with `model_config = ConfigDict(from_attributes=True)` for ORM serialization

`UserResponse` is REMOVED and replaced by `UserPublic`. The REST API response JSON shape MUST be identical — the rename is Python-only.

#### Scenario: UserPublic has five fields

- **WHEN** `uv run python -c "from app.schemas.user import UserPublic; print(sorted(UserPublic.model_fields.keys()))"` is run from `backend/`
- **THEN** the output is `['created_at', 'email', 'id', 'updated_at', 'username']`

#### Scenario: Router uses UserPublic not UserResponse

- **WHEN** `grep "UserResponse" backend/app/routers/users.py` is run
- **THEN** the command returns no output (UserResponse is no longer referenced)

### Requirement: CRUD router at /api/users

The `backend/app/routers/users.py` SHALL be updated to import `UserPublic` instead of `UserResponse` in all `response_model=` arguments and return-type annotations. No endpoint path, HTTP method, status code, or JSON field name changes.

#### Scenario: All five endpoints still reachable after refactor

- **WHEN** the backend starts after the SQLModel migration and `GET /api/users` is called
- **THEN** the response status is `200` and the body is a JSON array (confirming the router is registered and the schema serializes correctly)
