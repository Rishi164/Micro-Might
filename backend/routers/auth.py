import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pymongo.errors import DuplicateKeyError

from lib.db import db
from lib.security import clear_session, create_session, get_current_user_optional, hash_password, public_user, require_user, verify_password
from models.auth import AuthResponse, CustomerAddressUpdate, CustomerLoginRequest, CustomerSignupRequest, SessionState, UserPublic

router = APIRouter()


@router.post("/auth/signup", response_model=AuthResponse)
async def signup(payload: CustomerSignupRequest, request: Request, response: Response) -> AuthResponse:
    document = {
        "id": str(uuid.uuid4()),
        "name": payload.name.strip(),
        "email": str(payload.email).lower(),
        "phone": payload.phone.strip(),
        "role": "customer",
        "home_address": None,
        "home_pincode": None,
        "home_distance_km": None,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await db.users.insert_one(document)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    await create_session(request, response, document["id"])
    return AuthResponse(authenticated=True, user=public_user(document))


@router.post("/auth/login", response_model=AuthResponse)
async def login(payload: CustomerLoginRequest, request: Request, response: Response) -> AuthResponse:
    user = await db.users.find_one({"email": str(payload.email).lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await create_session(request, response, user["id"])
    return AuthResponse(authenticated=True, user=public_user(user))


@router.get("/auth/me", response_model=UserPublic)
async def me(user: dict = Depends(require_user)) -> UserPublic:
    return public_user(user)


@router.get("/auth/session", response_model=SessionState)
async def session_state(user: dict | None = Depends(get_current_user_optional)) -> SessionState:
    return SessionState(user=public_user(user) if user else None)


@router.put("/auth/address", response_model=UserPublic)
async def update_home_address(payload: CustomerAddressUpdate, user: dict = Depends(require_user)) -> UserPublic:
    if user.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customer account required")
    updates = {
        "home_address": payload.home_address.strip(),
        "home_pincode": payload.home_pincode,
        "home_distance_km": payload.home_distance_km,
    }
    await db.users.update_one({"id": user["id"]}, {"$set": updates})
    user.update(updates)
    return public_user(user)


@router.post("/auth/logout", status_code=204)
async def logout(request: Request, response: Response) -> None:
    await clear_session(request, response)