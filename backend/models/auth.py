from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


UserRole = Literal["customer", "admin"]


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    username: str | None = None
    phone: str | None = None
    created_at: datetime


class CustomerSignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=128)


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    authenticated: bool
    user: UserPublic


class SessionState(BaseModel):
    user: UserPublic | None = None


class AdminCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9._-]+$")
    password: str = Field(min_length=8, max_length=128)