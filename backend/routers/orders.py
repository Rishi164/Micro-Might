import math
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from lib.catalog import CATALOG
from lib.db import db
from lib.email_service import send_new_order_notifications, send_order_status_notification
from lib.security import get_current_user_optional, require_admin, require_user
from models.orders import Order, OrderAdminUpdate, OrderCreate, OrderItem

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


@router.post("/orders", response_model=Order, status_code=201)
async def create_order(payload: OrderCreate, user: dict | None = Depends(get_current_user_optional)) -> Order:
    items = _priced_items(payload)
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
        "payment_method": payload.payment_method,
        "payment_reference": payload.payment_reference.strip() if payload.payment_reference else None,
        "payment_status": "cod_due" if payload.payment_method == "cod" else "awaiting_verification",
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
    email_status = await send_new_order_notifications(document)
    document["email_status"] = email_status
    await db.orders.update_one({"id": document["id"]}, {"$set": {"email_status": email_status}})
    return _to_order(document)


@router.get("/orders/mine", response_model=list[Order])
async def my_orders(user: dict = Depends(require_user)) -> list[Order]:
    orders = await db.orders.find({"customer_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [_to_order(order) for order in orders]


@router.get("/admin/orders", response_model=list[Order])
async def admin_orders(_: dict = Depends(require_admin)) -> list[Order]:
    orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [_to_order(order) for order in orders]


@router.patch("/admin/orders/{order_id}", response_model=Order)
async def update_order(order_id: str, payload: OrderAdminUpdate, _: dict = Depends(require_admin)) -> Order:
    existing = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")
    now = datetime.now(timezone.utc)
    total = existing["subtotal"] + existing["cod_fee"] + payload.approved_delivery_fee
    updates = {
        "status": payload.status,
        "approved_delivery_fee": payload.approved_delivery_fee,
        "total": total,
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