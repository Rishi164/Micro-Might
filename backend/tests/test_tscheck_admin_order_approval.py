"""Criterion: Admin order management and delivery approval work.

Primary admin logs in, creates ONE fixture order, approves it with a delivery fee, and
the test asserts the recalculated final total/status and that a status-update email was
attempted. Also asserts an unauthenticated admin listing call is rejected.
"""

import httpx

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "micromight2026"


def test_admin_approves_order_and_recalculates_total(client):
    order_payload = {
        "customer_name": "Tscheck Admin Approval",
        "customer_email": "delivered@resend.dev",
        "customer_phone": "9900055566",
        "delivery_address": "3 Tscheck Approval Way, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 6,
        "preferred_delivery_date": "2026-12-20",
        "payment_method": "cod",
        "payment_reference": None,
        "notes": None,
        "items": [{"product_slug": "crimson-root", "plan": "regular", "weight": "50g", "quantity": 1}],
    }
    created = client.post("/orders", json=order_payload)
    assert created.status_code == 201, created.text
    order = created.json()
    assert order["subtotal"] == 119
    assert order["cod_fee"] == 30

    admin_login = client.post("/admin/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert admin_login.status_code == 200, admin_login.text

    listing = client.get("/admin/orders")
    assert listing.status_code == 200, listing.text
    assert any(row["id"] == order["id"] for row in listing.json())

    update = client.patch(
        f"/admin/orders/{order['id']}",
        json={
            "status": "confirmed",
            "approved_delivery_fee": 36,
            "approved_harvest_date": "2026-12-18",
            "approved_delivery_date": "2026-12-20",
        },
    )
    assert update.status_code == 200, update.text
    updated = update.json()
    assert updated["status"] == "confirmed"
    assert updated["approved_delivery_fee"] == 36
    assert updated["total"] == 119 + 30 + 36
    assert updated["email_status"].get("status_update") in ("sent", "failed")


def test_unauthenticated_admin_listing_rejected(backend_url):
    with httpx.Client(base_url=f"{backend_url}/api", timeout=30.0) as anon_client:
        response = anon_client.get("/admin/orders")
    assert response.status_code in (401, 403), response.text
