"""Criterion: Guest checkout creates a stored, server-priced order and sends notifications.

Creates ONE fixture order as a guest (no auth) and asserts the server recomputed canonical
catalog pricing, the free-5km / ₹9-per-extra-km delivery estimate, the ₹30 COD fee, the
pending_approval status, and that both customer/owner notification emails were attempted.
"""

import math

GUEST_EMAIL = "delivered@resend.dev"


def test_guest_checkout_creates_server_priced_order(client):
    payload = {
        "customer_name": "Tscheck Guest Pricing",
        "customer_email": GUEST_EMAIL,
        "customer_phone": "9900033344",
        "delivery_address": "77 Tscheck Pricing Lane, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 9,
        "preferred_delivery_date": "2026-12-20",
        "payment_method": "cod",
        "payment_reference": None,
        "notes": None,
        "items": [
            {"product_slug": "emerald-crown", "plan": "gyoc", "weight": "100g", "quantity": 2},
        ],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 201, response.text
    order = response.json()

    # Canonical catalog price for emerald-crown gyoc 100g is 239 (server computed, client never sent a price)
    assert order["items"][0]["unit_price"] == 239
    assert order["items"][0]["line_total"] == 478
    assert order["subtotal"] == 478

    extra_km = max(0, math.ceil(9 - 5))
    expected_delivery = extra_km * 9
    assert order["estimated_delivery_fee"] == expected_delivery
    assert order["cod_fee"] == 30
    assert order["total"] == 478 + expected_delivery + 30

    assert order["status"] == "pending_approval"
    assert order["preferred_delivery_date"] == "2026-12-20"
    assert order["approved_delivery_fee"] is None
    assert order["order_number"].startswith("MM-")
    assert order["email_status"]["customer"] in ("sent", "failed")
    assert order["email_status"]["owner"] in ("sent", "failed")
    # At minimum, the app must have attempted both notifications (not silently skipped)
    assert "customer" in order["email_status"] and "owner" in order["email_status"]


def test_invalid_product_slug_rejected(client):
    payload = {
        "customer_name": "Tscheck Invalid Product",
        "customer_email": GUEST_EMAIL,
        "customer_phone": "9900033344",
        "delivery_address": "77 Tscheck Pricing Lane, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 2,
        "payment_method": "qr",
        "payment_reference": None,
        "notes": None,
        "items": [
            {"product_slug": "not-a-real-product", "plan": "regular", "weight": "50g", "quantity": 1},
        ],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 422, response.text


def test_cod_is_rejected_outside_bengaluru(client):
    payload = {
        "customer_name": "Tscheck Outside Bengaluru",
        "customer_email": GUEST_EMAIL,
        "customer_phone": "9900033345",
        "delivery_address": "77 Test Lane, New Delhi",
        "pincode": "110001",
        "estimated_distance_km": 2,
        "preferred_delivery_date": "2026-12-20",
        "payment_method": "cod",
        "items": [
            {"product_slug": "emerald-crown", "plan": "regular", "weight": "50g", "quantity": 1},
        ],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 422, response.text
    assert "only in Bengaluru" in response.json()["detail"]


def test_razorpay_orders_cannot_bypass_payment_verification(client):
    payload = {
        "customer_name": "Tscheck Razorpay",
        "customer_email": GUEST_EMAIL,
        "customer_phone": "9900033346",
        "delivery_address": "77 Test Lane, Bengaluru",
        "pincode": "560083",
        "estimated_distance_km": 2,
        "preferred_delivery_date": "2026-12-20",
        "payment_method": "razorpay",
        "items": [
            {"product_slug": "emerald-crown", "plan": "regular", "weight": "50g", "quantity": 1},
        ],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 422, response.text
    assert "verified Razorpay" in response.json()["detail"]


def test_razorpay_config_reports_readiness_without_exposing_secrets(client):
    response = client.get("/payments/razorpay/config")
    assert response.status_code == 200, response.text
    assert isinstance(response.json().get("enabled"), bool)
    assert "key_secret" not in response.json()


def test_legacy_qr_is_rejected_for_new_orders(client):
    payload = {
        "customer_name": "Tscheck Legacy QR",
        "customer_email": GUEST_EMAIL,
        "customer_phone": "9900033347",
        "delivery_address": "77 Test Lane, Bengaluru",
        "pincode": "560083",
        "estimated_distance_km": 2,
        "preferred_delivery_date": "2026-12-20",
        "payment_method": "qr",
        "items": [
            {"product_slug": "emerald-crown", "plan": "regular", "weight": "50g", "quantity": 1},
        ],
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 422, response.text
