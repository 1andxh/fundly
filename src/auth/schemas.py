import uuid
from datetime import datetime
from pydantic import EmailStr, BaseModel, Field, ConfigDict


class UserCreateModel(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8, description="Password must be at least 8 characters"
    )
    full_name: str = Field(min_length=2, max_length=100)
    phone_number: str | None = None


class UserLoginModel(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


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
