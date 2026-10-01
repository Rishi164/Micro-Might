"""Criterion: Signed-in customers can save a reusable home delivery address.

Signs up a fresh customer, PUTs /auth/address, re-fetches /auth/session to confirm the
values persisted server-side (simulating logout/login), and asserts a non-customer-owned
(unauthenticated) call is rejected.
"""

import uuid

import httpx


def _unique_email() -> str:
    return f"tscheck-address-{uuid.uuid4().hex[:10]}@example.com"


def test_customer_saves_and_persists_home_address(client):
    email = _unique_email()
    signup = client.post("/auth/signup", json={
        "name": "Tscheck Address Customer",
        "email": email,
        "phone": "9900012345",
        "password": "AddressTest2026!",
    })
    assert signup.status_code == 200, signup.text

    update = client.put("/auth/address", json={
        "home_address": "88 Doorstep Lane, Gottigere, Bengaluru",
        "home_pincode": "560083",
        "home_distance_km": 7.2,
    })
    assert update.status_code == 200, update.text
    user = update.json()
    assert user["home_address"] == "88 Doorstep Lane, Gottigere, Bengaluru"
    assert user["home_pincode"] == "560083"
    assert user["home_distance_km"] == 7.2

    # Simulate logout/login by re-logging in with a fresh client and checking the saved values persisted.
    with httpx.Client(base_url=client.base_url, timeout=30.0) as fresh_client:
        login = fresh_client.post("/auth/login", json={"email": email, "password": "AddressTest2026!"})
        assert login.status_code == 200, login.text
        me = fresh_client.get("/auth/me")
        assert me.status_code == 200, me.text
        persisted = me.json()
        assert persisted["home_address"] == "88 Doorstep Lane, Gottigere, Bengaluru"
        assert persisted["home_pincode"] == "560083"
        assert persisted["home_distance_km"] == 7.2


def test_unauthenticated_address_update_rejected(backend_url):
    with httpx.Client(base_url=f"{backend_url}/api", timeout=30.0) as anon_client:
        response = anon_client.put("/auth/address", json={
            "home_address": "1 Nowhere Street, Bengaluru",
            "home_pincode": "560001",
            "home_distance_km": 3,
        })
    assert response.status_code in (401, 403), response.text
