import math
import secrets
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.catalog import CATALOG
from lib.db import db
from lib.email_service import send_new_order_notifications, send_order_status_notification
from lib.inventory import ensure_inventory, inventory_list
from lib.dates import today_iso
from lib.security import get_current_user_optional, require_admin, require_user
from models.orders import InventoryItem, InventoryUpdate, Order, OrderAdminUpdate, OrderCreate, OrderItem

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


@router.post("/orders", response_model=Order, status_code=201)
async def create_order(payload: OrderCreate, user: dict | None = Depends(get_current_user_optional)) -> Order:
    items = _priced_items(payload)
    await _check_stock(items)
    today = date.fromisoformat(today_iso())
    if payload.preferred_delivery_date < today:
        raise HTTPException(status_code=422, detail="Preferred delivery date cannot be in the past")
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


@router.get("/orders/mine", response_model=list[Order])
async def my_orders(user: dict = Depends(require_user)) -> list[Order]:
    orders = await db.orders.find({"customer_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return [_to_order(order) for order in orders]


@router.get("/admin/orders", response_model=list[Order])
async def admin_orders(
    status: Literal["pending_approval", "confirmed", "cancelled"] | None = Query(default=None),
    payment_method: Literal["qr", "cod"] | None = Query(default=None),
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