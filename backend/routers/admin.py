import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from lib.db import db
from models.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    PaymentQr,
    PaymentQrUpdate,
)

router = APIRouter()

DEFAULT_PAYMENT_QR = "https://customer-assets-4nw71qhi.emergentagent.net/job_fresh-from-trays/artifacts/zncy8do5_image.png"


def _credentials_match(username: str, password: str) -> bool:
    return username == os.environ.get("ADMIN_DEMO_USERNAME") and password == os.environ.get("ADMIN_DEMO_PASSWORD")


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest) -> AdminLoginResponse:
    return AdminLoginResponse(authenticated=_credentials_match(payload.username, payload.password))


@router.get("/payment-qr", response_model=PaymentQr)
async def get_payment_qr() -> PaymentQr:
    document = await db.payment_qr.find_one({"key": "primary"})
    if not document:
        return PaymentQr(qr_data_url=DEFAULT_PAYMENT_QR)
    return PaymentQr(qr_data_url=document.get("qr_data_url"), updated_at=document.get("updated_at"))


@router.put("/payment-qr", response_model=PaymentQr)
async def update_payment_qr(payload: PaymentQrUpdate) -> PaymentQr:
    if not _credentials_match(payload.admin_username, payload.admin_password):
        raise HTTPException(status_code=401, detail="Invalid demo admin credentials")

    updated_at = datetime.now(timezone.utc)
    await db.payment_qr.update_one(
        {"key": "primary"},
        {"$set": {"key": "primary", "qr_data_url": payload.qr_data_url, "updated_at": updated_at}},
        upsert=True,
    )
    return PaymentQr(qr_data_url=payload.qr_data_url, updated_at=updated_at)