import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import Column
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(sa.Uuid, primary_key=True, default=uuid.uuid4),
    )
    username: str = Field(
        sa_column=Column(sa.String(128), unique=True, nullable=False)
    )
    email: str = Field(
        sa_column=Column(sa.String(256), unique=True, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(sa.DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(sa.DateTime(timezone=True), nullable=False),
    )
