import hashlib
import hmac
import math
import os
import secrets
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ReturnDocument

from lib.catalog import CATALOG
from lib.db import db
from lib.email_service import send_new_order_notifications, send_order_status_notification
from lib.inventory import ensure_inventory, inventory_list
from lib.dates import today_iso
from lib.security import get_current_user_optional, require_admin, require_user
from models.orders import (
    InventoryItem,
    InventoryUpdate,
    Order,
    OrderAdminUpdate,
    OrderCreate,
    OrderItem,
    RazorpayConfig,
    RazorpayOrderResponse,
    RazorpayVerifyRequest,
)

router = APIRouter()


def _to_order(document: dict) -> Order:
    return Order(**{key: value for key, value in document.items() if key != "_id"})


def _priced_items(payload: OrderCreate) -> list[OrderItem]:
    items: list[OrderItem] = []
    for requested in payload.items:
        product = CATALOG.get(requested.product_slug)
        if not product or requested.plan not in product:
            raise HTTPException(status_code=422, detail=f"Invalid product or pricing plan: {requested.product_slug}")
        unit_price = product[requested.plan][requested.weight]
        items.append(OrderItem(
            product_slug=requested.product_slug,
            name=product["name"],
            variety=product["variety"],
            plan=requested.plan,
            weight=requested.weight,
            quantity=requested.quantity,
            unit_price=unit_price,
            line_total=unit_price * requested.quantity,
        ))
    return items


async def _check_stock(items: list[OrderItem]) -> None:
    for item in items:
        if item.plan != "regular":
            continue
        inventory = await db.inventory.find_one({"product_slug": item.product_slug})
        if not inventory or not inventory.get("tracking_enabled"):
            continue
        field = "stock_50g" if item.weight == "50g" else "stock_100g"
        if inventory.get(field, 0) < item.quantity:
            raise HTTPException(status_code=409, detail=f"Not enough {item.name} {item.weight} packs in stock")


async def _deduct_stock(items: list[dict]) -> None:
    await _check_stock([OrderItem(**item) for item in items])
    for item in items:
        if item["plan"] != "regular":
            continue
        inventory = await db.inventory.find_one({"product_slug": item["product_slug"]})
        if not inventory or not inventory.get("tracking_enabled"):
            continue
        field = "stock_50g" if item["weight"] == "50g" else "stock_100g"
        await db.inventory.update_one(
            {"product_slug": item["product_slug"]},
            {"$inc": {field: -item["quantity"]}, "$set": {"updated_at": datetime.now(timezone.utc)}},
        )


def _validate_order(payload: OrderCreate) -> list[OrderItem]:
    items = _priced_items(payload)
    today = date.fromisoformat(today_iso())
    if payload.preferred_delivery_date < today:
        raise HTTPException(status_code=422, detail="Preferred delivery date cannot be in the past")
    if payload.payment_method == "cod" and not payload.pincode.startswith("560"):
        raise HTTPException(status_code=422, detail="Cash on Delivery is available only in Bengaluru")
    return items


@router.get("/payments/razorpay/config", response_model=RazorpayConfig)
async def razorpay_config() -> RazorpayConfig:
    return RazorpayConfig(
        enabled=bool(os.environ.get("RAZORPAY_KEY_ID", "").strip() and os.environ.get("RAZORPAY_KEY_SECRET", "").strip()),
    )


async def _save_order(payload: OrderCreate, user: dict | None, items: list[OrderItem]) -> Order:
    await _check_stock(items)
    subtotal = sum(item.line_total for item in items)
    extra_km = max(0, math.ceil(payload.estimated_distance_km - 5))
    estimated_delivery_fee = extra_km * 9
    cod_fee = 30 if payload.payment_method == "cod" else 0
    now = datetime.now(timezone.utc)
    document = {
        "id": str(uuid.uuid4()),
        "order_number": f"MM-{now.strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}",
        "customer_id": user["id"] if user and user.get("role") == "customer" else None,
        "customer_name": payload.customer_name.strip(),
        "customer_email": str(payload.customer_email).lower(),
        "customer_phone": payload.customer_phone.strip(),
        "delivery_address": payload.delivery_address.strip(),
        "pincode": payload.pincode,
        "estimated_distance_km": payload.estimated_distance_km,
        "preferred_delivery_date": payload.preferred_delivery_date.isoformat(),
        "approved_harvest_date": None,
        "approved_delivery_date": None,
        "payment_method": payload.payment_method,
        "payment_reference": payload.payment_reference.strip() if payload.payment_reference else None,
        "payment_status": "cod_due" if payload.payment_method == "cod" else "paid" if payload.payment_method == "razorpay" else "awaiting_verification",
        "status": "pending_approval",
        "items": [item.model_dump() for item in items],
        "subtotal": subtotal,
        "cod_fee": cod_fee,
        "estimated_delivery_fee": estimated_delivery_fee,
        "approved_delivery_fee": None,
        "total": subtotal + cod_fee + estimated_delivery_fee,
        "notes": payload.notes.strip() if payload.notes else None,
        "email_status": {"customer": "pending", "owner": "pending"},
        "created_at": now,
        "updated_at": now,
    }
    await db.orders.insert_one(document)
    if user and user.get("role") == "customer" and payload.save_address:
        await db.users.update_one({"id": user["id"]}, {"$set": {
            "home_address": payload.delivery_address.strip(),
            "home_pincode": payload.pincode,
            "home_distance_km": payload.estimated_distance_km,
        }})
    email_status = await send_new_order_notifications(document)
    document["email_status"] = email_status
    await db.orders.update_one({"id": document["id"]}, {"$set": {"email_status": email_status}})
    return _to_order(document)


@router.post("/payments/razorpay/order", response_model=RazorpayOrderResponse)
async def create_razorpay_order(
    payload: OrderCreate,
    user: dict | None = Depends(get_current_user_optional),
) -> RazorpayOrderResponse:
    key_id = os.environ.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret:
        raise HTTPException(status_code=503, detail="Razorpay is not configured")
    if payload.payment_method != "razorpay":
        raise HTTPException(status_code=422, detail="Razorpay checkout requires Razorpay as the payment method")

    items = _validate_order(payload)
    await _check_stock(items)
    subtotal = sum(item.line_total for item in items)
    delivery_fee = max(0, math.ceil(payload.estimated_distance_km - 5)) * 9
    amount = (subtotal + delivery_fee) * 100
    receipt = str(uuid.uuid4())
    try:
        async with httpx.AsyncClient(timeout=15) as gateway:
            response = await gateway.post(
                "https://api.razorpay.com/v1/orders",
                auth=(key_id, key_secret),
                json={"amount": amount, "currency": "INR", "receipt": receipt},
            )
            response.raise_for_status()
            gateway_order = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not start Razorpay checkout") from exc

    now = datetime.now(timezone.utc)
    await db.payment_intents.insert_one({
        "razorpay_order_id": gateway_order["id"],
        "amount": amount,
        "payload": payload.model_dump(mode="json"),
        "customer_id": user["id"] if user and user.get("role") == "customer" else None,
        "status": "created",
        "created_at": now,
        "expires_at": now + timedelta(minutes=30),
    })
    return RazorpayOrderResponse(key_id=key_id, order_id=gateway_order["id"], amount=amount, currency="INR")


@router.post("/payments/razorpay/verify", response_model=Order)
async def verify_razorpay_payment(payload: RazorpayVerifyRequest) -> Order:
    key_id = os.environ.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret:
        raise HTTPException(status_code=503, detail="Razorpay is not configured")

    intent = await db.payment_intents.find_one({"razorpay_order_id": payload.razorpay_order_id})
    if not intent:
        raise HTTPException(status_code=404, detail="Razorpay order was not found or has expired")

    signed_payload = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode()
    expected_signature = hmac.new(key_secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Razorpay payment signature is invalid")

    if intent["status"] == "completed":
        existing = await db.orders.find_one({"id": intent.get("order_id")}, {"_id": 0})
        if existing:
            return _to_order(existing)
    try:
        async with httpx.AsyncClient(timeout=15) as gateway:
            response = await gateway.get(
                f"https://api.razorpay.com/v1/payments/{payload.razorpay_payment_id}",
                auth=(key_id, key_secret),
            )
            response.raise_for_status()
            payment = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Could not verify the Razorpay payment") from exc

    if (
        payment.get("order_id") != payload.razorpay_order_id
        or payment.get("amount") != intent["amount"]
        or payment.get("status") != "captured"
    ):
        raise HTTPException(status_code=400, detail="Razorpay payment has not been captured for this order")

    claimed = await db.payment_intents.find_one_and_update(
        {"razorpay_order_id": payload.razorpay_order_id, "status": "created"},
        {"$set": {"status": "processing", "payment_id": payload.razorpay_payment_id}},
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        raise HTTPException(status_code=409, detail="This Razorpay payment is already being processed")

    order_payload = OrderCreate.model_validate(claimed["payload"]).model_copy(
        update={"payment_reference": payload.razorpay_payment_id},
    )
    user = await db.users.find_one({"id": claimed.get("customer_id")}, {"_id": 0}) if claimed.get("customer_id") else None
    try:
        items = _validate_order(order_payload)
        order = await _save_order(order_payload, user, items)
    except Exception:
        await db.payment_intents.update_one(
            {"razorpay_order_id": payload.razorpay_order_id, "status": "processing"},
            {"$set": {"status": "created"}, "$unset": {"payment_id": ""}},
        )
        raise
    await db.payment_intents.update_one(
        {"razorpay_order_id": payload.razorpay_order_id},
        {"$set": {"status": "completed", "order_id": order.id}},
    )
    return order


@router.post("/orders", response_model=Order, status_code=201)
async def create_order(payload: OrderCreate, user: dict | None = Depends(get_current_user_optional)) -> Order:
    if payload.payment_method == "razorpay":
        raise HTTPException(status_code=422, detail="Use the verified Razorpay checkout flow")
    items = _validate_order(payload)
    return await _save_order(payload, user, items)


@router.get("/orders/mine", response_model=list[Order])
async def my_orders(user: dict = Depends(require_user)) -> list[Order]:
    orders = await db.orders.find({"customer_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [_to_order(order) for order in orders]


@router.get("/admin/orders", response_model=list[Order])
async def admin_orders(
    status: Literal["pending_approval", "confirmed", "cancelled"] | None = Query(default=None),
    payment_method: Literal["qr", "razorpay", "cod"] | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: dict = Depends(require_admin),
) -> list[Order]:
    query: dict = {}
    if status:
        query["status"] = status
    if payment_method:
        query["payment_method"] = payment_method
    if date_from or date_to:
        created_filter: dict = {}
        if date_from:
            created_filter["$gte"] = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        if date_to:
            created_filter["$lt"] = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
        query["created_at"] = created_filter
    orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [_to_order(order) for order in orders]


@router.patch("/admin/orders/{order_id}", response_model=Order)
async def update_order(order_id: str, payload: OrderAdminUpdate, _: dict = Depends(require_admin)) -> Order:
    existing = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    if existing["status"] != "pending_approval":
        raise HTTPException(status_code=409, detail="This order has already been finalized")
    if payload.status == "confirmed":
        if not payload.approved_harvest_date or not payload.approved_delivery_date:
            raise HTTPException(status_code=422, detail="Harvest and delivery dates are required for confirmation")
        if payload.approved_delivery_date < payload.approved_harvest_date:
            raise HTTPException(status_code=422, detail="Delivery date cannot be before harvest date")
        await _deduct_stock(existing["items"])
    now = datetime.now(timezone.utc)
    total = existing["subtotal"] + existing["cod_fee"] + payload.approved_delivery_fee
    updates = {
        "status": payload.status,
        "approved_delivery_fee": payload.approved_delivery_fee,
        "total": total,
        "approved_harvest_date": payload.approved_harvest_date.isoformat() if payload.approved_harvest_date else None,
        "approved_delivery_date": payload.approved_delivery_date.isoformat() if payload.approved_delivery_date else None,
        "updated_at": now,
    }
    await db.orders.update_one({"id": order_id}, {"$set": updates})
    existing.update(updates)
    try:
        existing["email_status"]["status_update"] = await send_order_status_notification(existing)
    except Exception:
        existing["email_status"]["status_update"] = "failed"
    await db.orders.update_one({"id": order_id}, {"$set": {"email_status": existing["email_status"]}})
    return _to_order(existing)


@router.get("/inventory", response_model=list[InventoryItem])
async def public_inventory() -> list[InventoryItem]:
    return [InventoryItem(**item) for item in await inventory_list()]


@router.get("/admin/inventory", response_model=list[InventoryItem])
async def admin_inventory(_: dict = Depends(require_admin)) -> list[InventoryItem]:
    return [InventoryItem(**item) for item in await inventory_list()]


@router.put("/admin/inventory/{product_slug}", response_model=InventoryItem)
async def update_inventory(product_slug: str, payload: InventoryUpdate, _: dict = Depends(require_admin)) -> InventoryItem:
    if product_slug not in CATALOG:
        raise HTTPException(status_code=404, detail="Product not found")
    await ensure_inventory()
    updates = {
        "tracking_enabled": payload.tracking_enabled,
        "stock_50g": payload.stock_50g,
        "stock_100g": payload.stock_100g,
        "updated_at": datetime.now(timezone.utc),
    }
    document = await db.inventory.find_one_and_update(
        {"product_slug": product_slug},
        {"$set": updates},
        return_document=True,
        projection={"_id": 0},
    )
    return InventoryItem(**document)