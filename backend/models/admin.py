from datetime import datetime

from pydantic import BaseModel, Field

from models.auth import UserPublic


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    authenticated: bool
    user: UserPublic


class PaymentQr(BaseModel):
    qr_data_url: str | None = None
    updated_at: datetime | None = None


class PaymentQrUpdate(BaseModel):
    qr_data_url: str = Field(min_length=20)