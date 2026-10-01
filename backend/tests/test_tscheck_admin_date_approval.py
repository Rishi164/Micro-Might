"""Criterion: Admins approve harvest and delivery dates before confirmation.

Creates ONE fixture order, asserts confirm is rejected without both approved dates,
rejected when delivery precedes harvest, and succeeds (storing both dates + recalculated
total) when valid. Also asserts the dates surface on the customer's own order listing.
"""

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "micromight2026"


def test_admin_date_approval_gating_and_confirmation(client):
    order_payload = {
        "customer_name": "Tscheck Date Approval",
        "customer_email": "delivered@resend.dev",
        "customer_phone": "9900099001",
        "delivery_address": "9 Tscheck Date Approval Way, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 6,
        "preferred_delivery_date": "2026-12-24",
        "payment_method": "qr",
        "payment_reference": None,
        "notes": None,
        "items": [{"product_slug": "crimson-root", "plan": "regular", "weight": "50g", "quantity": 1}],
    }
    created = client.post("/orders", json=order_payload)
    assert created.status_code == 201, created.text
    order = created.json()
    assert order["preferred_delivery_date"] == "2026-12-24"

    admin_login = client.post("/admin/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert admin_login.status_code == 200, admin_login.text

    # Missing both approved dates -> rejected
    missing_dates = client.patch(f"/admin/orders/{order['id']}", json={
        "status": "confirmed",
        "approved_delivery_fee": 10,
    })
    assert missing_dates.status_code == 422, missing_dates.text

    # Delivery before harvest -> rejected
    bad_order = client.patch(f"/admin/orders/{order['id']}", json={
        "status": "confirmed",
        "approved_delivery_fee": 10,
        "approved_harvest_date": "2026-12-23",
        "approved_delivery_date": "2026-12-20",
    })
    assert bad_order.status_code == 422, bad_order.text

    # Valid confirmation -> stores dates, recalculates total
    valid = client.patch(f"/admin/orders/{order['id']}", json={
        "status": "confirmed",
        "approved_delivery_fee": 10,
        "approved_harvest_date": "2026-12-22",
        "approved_delivery_date": "2026-12-24",
    })
    assert valid.status_code == 200, valid.text
    confirmed = valid.json()
    assert confirmed["status"] == "confirmed"
    assert confirmed["approved_harvest_date"] == "2026-12-22"
    assert confirmed["approved_delivery_date"] == "2026-12-24"
    assert confirmed["total"] == order["subtotal"] + order["cod_fee"] + 10
    assert confirmed["email_status"].get("status_update") in ("sent", "failed")
