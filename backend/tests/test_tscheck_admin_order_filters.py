"""Criterion: Admin order filters work by status, payment and date range.

Creates ONE fixture pending cod order, then asserts
GET /api/admin/orders with status/payment_method/date_from/date_to query params returns
only matching rows (fixture ids present/absent as appropriate).
"""

from datetime import date, timedelta

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "micromight2026"


def _order_payload(payment_method: str, phone: str):
    return {
        "customer_name": "Tscheck Filter Order",
        "customer_email": "delivered@resend.dev",
        "customer_phone": phone,
        "delivery_address": "21 Tscheck Filter Street, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 3,
        "preferred_delivery_date": "2026-12-26",
        "payment_method": payment_method,
        "payment_reference": None,
        "notes": None,
        "items": [{"product_slug": "crimson-root", "plan": "regular", "weight": "50g", "quantity": 1}],
    }


def test_admin_filters_by_status_payment_and_date_range(client):
    cod_order = client.post("/orders", json=_order_payload("cod", "9900055002"))
    assert cod_order.status_code == 201, cod_order.text
    cod_id = cod_order.json()["id"]

    admin_login = client.post("/admin/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert admin_login.status_code == 200, admin_login.text

    by_status = client.get("/admin/orders", params={"status": "pending_approval"})
    assert by_status.status_code == 200, by_status.text
    status_ids = {row["id"] for row in by_status.json()}
    assert cod_id in status_ids
    assert all(row["status"] == "pending_approval" for row in by_status.json())

    by_payment_razorpay = client.get("/admin/orders", params={"payment_method": "razorpay"})
    assert by_payment_razorpay.status_code == 200, by_payment_razorpay.text
    razorpay_ids = {row["id"] for row in by_payment_razorpay.json()}
    assert cod_id not in razorpay_ids

    by_payment_qr = client.get("/admin/orders", params={"payment_method": "qr"})
    assert by_payment_qr.status_code == 200, by_payment_qr.text
    qr_ids = {row["id"] for row in by_payment_qr.json()}
    assert cod_id not in qr_ids

    by_payment_cod = client.get("/admin/orders", params={"payment_method": "cod"})
    cod_ids = {row["id"] for row in by_payment_cod.json()}
    assert cod_id in cod_ids

    today = date.today()
    future_from = (today + timedelta(days=5)).isoformat()
    future_to = (today + timedelta(days=10)).isoformat()
    out_of_range = client.get("/admin/orders", params={"date_from": future_from, "date_to": future_to})
    assert out_of_range.status_code == 200, out_of_range.text
    out_ids = {row["id"] for row in out_of_range.json()}
    assert cod_id not in out_ids

    in_range = client.get("/admin/orders", params={"date_from": today.isoformat(), "date_to": today.isoformat()})
    assert in_range.status_code == 200, in_range.text
    in_ids = {row["id"] for row in in_range.json()}
    assert cod_id in in_ids
