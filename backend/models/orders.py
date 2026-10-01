from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


OrderPlan = Literal["regular", "gyoc"]
OrderWeight = Literal["50g", "100g"]
PaymentMethod = Literal["qr", "cod"]
OrderStatus = Literal["pending_approval", "confirmed", "cancelled"]


class CartItemRequest(BaseModel):
    product_slug: str
    plan: OrderPlan
    weight: OrderWeight
    quantity: int = Field(ge=1, le=20)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=80)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=10, max_length=15)
    delivery_address: str = Field(min_length=12, max_length=400)
    pincode: str = Field(min_length=6, max_length=6, pattern=r"^[0-9]{6}$")
    estimated_distance_km: float = Field(ge=0, le=100)
    payment_method: PaymentMethod
    payment_reference: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)
    items: list[CartItemRequest] = Field(min_length=1, max_length=30)


class OrderItem(BaseModel):
    product_slug: str
    name: str
    variety: str
    plan: OrderPlan
    weight: OrderWeight
    quantity: int
    unit_price: int
    line_total: int


class Order(BaseModel):
    id: str
    order_number: str
    customer_id: str | None = None
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    delivery_address: str
    pincode: str
    estimated_distance_km: float
    payment_method: PaymentMethod
    payment_reference: str | None = None
    payment_status: str
    status: OrderStatus
    items: list[OrderItem]
    subtotal: int
    cod_fee: int
    estimated_delivery_fee: int
    approved_delivery_fee: int | None = None
    total: int
    notes: str | None = None
    email_status: dict[str, str]
    created_at: datetime
    updated_at: datetime


class OrderAdminUpdate(BaseModel):
    status: Literal["confirmed", "cancelled"]
    approved_delivery_fee: int = Field(ge=0, le=5000)