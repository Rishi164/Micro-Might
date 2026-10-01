"""Criterion: Customers can request when they need an order.

Asserts checkout requires preferred_delivery_date, rejects a past date server-side, and
stores the requested date on a successfully created guest order.
"""

GUEST_EMAIL = "delivered@resend.dev"


def _base_payload(**overrides):
    payload = {
        "customer_name": "Tscheck Preferred Date",
        "customer_email": GUEST_EMAIL,
        "customer_phone": "9900077788",
        "delivery_address": "45 Tscheck Preferred Date Road, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 4,
        "preferred_delivery_date": "2026-12-25",
        "payment_method": "cod",
        "payment_reference": None,
        "notes": None,
        "items": [{"product_slug": "crimson-root", "plan": "regular", "weight": "50g", "quantity": 1}],
    }
    payload.update(overrides)
    return payload


def test_preferred_delivery_date_stored_on_order(client):
    response = client.post("/orders", json=_base_payload())
    assert response.status_code == 201, response.text
    order = response.json()
    assert order["preferred_delivery_date"] == "2026-12-25"


def test_missing_preferred_delivery_date_rejected(client):
    payload = _base_payload()
    del payload["preferred_delivery_date"]
    response = client.post("/orders", json=payload)
    assert response.status_code == 422, response.text


def test_past_preferred_delivery_date_rejected(client):
    response = client.post("/orders", json=_base_payload(preferred_delivery_date="2020-01-01"))
    assert response.status_code == 422, response.text
