import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pymongo.errors import DuplicateKeyError

from lib.db import db
from lib.security import create_session, hash_password, public_user, require_admin, verify_password
from models.auth import AdminCreateRequest, UserPublic
from models.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    PaymentQr,
    PaymentQrUpdate,
)

router = APIRouter()

DEFAULT_PAYMENT_QR = "https://customer-assets-4nw71qhi.emergentagent.net/job_fresh-from-trays/artifacts/zncy8do5_image.png"


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest, request: Request, response: Response) -> AdminLoginResponse:
    user = await db.users.find_one({"username": payload.username, "role": "admin"})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    await create_session(request, response, user["id"])
    return AdminLoginResponse(authenticated=True, user=public_user(user))


@router.get("/payment-qr", response_model=PaymentQr)
async def get_payment_qr() -> PaymentQr:
    document = await db.payment_qr.find_one({"key": "primary"})
    if not document:
        return PaymentQr(qr_data_url=DEFAULT_PAYMENT_QR)
    return PaymentQr(qr_data_url=document.get("qr_data_url"), updated_at=document.get("updated_at"))


@router.put("/payment-qr", response_model=PaymentQr)
async def update_payment_qr(payload: PaymentQrUpdate, _: dict = Depends(require_admin)) -> PaymentQr:
    updated_at = datetime.now(timezone.utc)
    await db.payment_qr.update_one(
        {"key": "primary"},
        {"$set": {"key": "primary", "qr_data_url": payload.qr_data_url, "updated_at": updated_at}},
        upsert=True,
    )
    return PaymentQr(qr_data_url=payload.qr_data_url, updated_at=updated_at)


@router.get("/admin/admins", response_model=list[UserPublic])
async def list_admins(_: dict = Depends(require_admin)) -> list[UserPublic]:
    admins = await db.users.find({"role": "admin"}, {"_id": 0}).sort("created_at", 1).to_list(100)
    return [public_user(admin) for admin in admins]


@router.post("/admin/admins", response_model=UserPublic, status_code=201)
async def create_admin(payload: AdminCreateRequest, _: dict = Depends(require_admin)) -> UserPublic:
    document = {
        "id": str(uuid.uuid4()),
        "name": payload.name.strip(),
        "email": str(payload.email).lower(),
        "username": payload.username.strip().lower(),
        "role": "admin",
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await db.users.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="Email or username is already in use") from exc
    return public_user(document)