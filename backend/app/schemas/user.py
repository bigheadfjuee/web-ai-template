import uuid
from datetime import datetime

from pydantic import ConfigDict, EmailStr
from sqlmodel import SQLModel


class UserBase(SQLModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserUpdate(SQLModel):
    username: str | None = None
    email: EmailStr | None = None


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
