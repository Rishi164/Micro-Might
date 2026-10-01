import base64
import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response

from lib.db import db
from models.auth import UserPublic

SESSION_COOKIE = "micro_might_session"
SESSION_DAYS = 30
PBKDF2_ITERATIONS = 390_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, iterations, salt, expected = encoded.split("$", 3)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(base64.b64encode(digest).decode(), expected)
    except (ValueError, TypeError):
        return False


def public_user(document: dict) -> UserPublic:
    return UserPublic(**{key: value for key, value in document.items() if key != "password_hash" and key != "_id"})


async def ensure_default_admin() -> None:
    username = os.environ["ADMIN_DEMO_USERNAME"]
    existing = await db.users.find_one({"username": username, "role": "admin"})
    if existing:
        return
    now = datetime.now(timezone.utc)
    await db.users.insert_one({
        "id": str(uuid.uuid4()),
        "name": "Micro Might Admin",
        "email": os.environ["OWNER_EMAIL"].lower(),
        "username": username,
        "phone": None,
        "role": "admin",
        "password_hash": hash_password(os.environ["ADMIN_DEMO_PASSWORD"]),
        "created_at": now,
    })


def _secure_cookie(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"


async def create_session(request: Request, response: Response, user_id: str) -> None:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=SESSION_DAYS)
    await db.sessions.insert_one({"token": token, "user_id": user_id, "created_at": now, "expires_at": expires_at})
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=_secure_cookie(request),
        samesite="lax",
        path="/",
    )


async def clear_session(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        await db.sessions.delete_one({"token": token})
    response.delete_cookie(SESSION_COOKIE, path="/", secure=_secure_cookie(request), samesite="lax")


async def get_current_user_optional(request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    session = await db.sessions.find_one({"token": token, "expires_at": {"$gt": datetime.now(timezone.utc)}})
    if not session:
        return None
    return await db.users.find_one({"id": session["user_id"]}, {"_id": 0})


async def require_user(user: dict | None = Depends(get_current_user_optional)) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Please sign in")
    return user


async def require_admin(user: dict = Depends(require_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user