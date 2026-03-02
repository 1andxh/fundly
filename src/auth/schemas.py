import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class UserCreateModel(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8, description="Password must be at least 8 characters"
    )
    full_name: str = Field(min_length=2, max_length=100)
    phone_number: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class UserLoginModel(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class UserResponseModel(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone_number: str | None
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
