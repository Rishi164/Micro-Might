"""Criterion: Optional customer authentication and order dashboard work.

Logs in as the reusable customer, places ONE order while authenticated, and asserts the
order is attributed to the session's customer_id and returned by /orders/mine. Also asserts
unauthenticated access to /orders/mine is rejected.
"""

import httpx

CUSTOMER_EMAIL = "delivered@resend.dev"
CUSTOMER_PASSWORD = "FreshGreens2026!"


def test_customer_sees_only_own_order_after_login(client):
    login = client.post("/auth/login", json={"email": CUSTOMER_EMAIL, "password": CUSTOMER_PASSWORD})
    assert login.status_code == 200, login.text
    user = login.json()["user"]
    assert user["role"] == "customer"

    order_payload = {
        "customer_name": "Tscheck Customer Ownership",
        "customer_email": CUSTOMER_EMAIL,
        "customer_phone": "9900044455",
        "delivery_address": "12 Tscheck Ownership Road, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 1,
        "payment_method": "qr",
        "payment_reference": None,
        "notes": None,
        "items": [{"product_slug": "golden-silk", "plan": "regular", "weight": "50g", "quantity": 1}],
    }
    created = client.post("/orders", json=order_payload)
    assert created.status_code == 201, created.text
    order = created.json()
    assert order["customer_id"] == user["id"]

    mine = client.get("/orders/mine")
    assert mine.status_code == 200, mine.text
    order_ids = [row["id"] for row in mine.json()]
    assert order["id"] in order_ids


def test_unauthenticated_order_history_rejected(backend_url):
    with httpx.Client(base_url=f"{backend_url}/api", timeout=30.0) as anon_client:
        response = anon_client.get("/orders/mine")
    assert response.status_code in (401, 403), response.text
