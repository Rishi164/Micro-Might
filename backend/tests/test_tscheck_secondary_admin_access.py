"""Criterion: Multiple admin access works.

The documented secondary operations admin can log in independently, the primary admin's
/admin/admins listing includes both accounts, and the owner-authenticated admin-creation
endpoint rejects unauthenticated/non-admin requests.
"""

import httpx

PRIMARY_USERNAME = "admin"
PRIMARY_PASSWORD = "micromight2026"
SECONDARY_USERNAME = "operations"
SECONDARY_PASSWORD = "GrowWithCare2026!"


def test_secondary_admin_logs_in_independently_and_is_listed(client, backend_url):
    secondary_login = client.post("/admin/login", json={"username": SECONDARY_USERNAME, "password": SECONDARY_PASSWORD})
    assert secondary_login.status_code == 200, secondary_login.text
    assert secondary_login.json()["user"]["username"] == SECONDARY_USERNAME

    with httpx.Client(base_url=f"{backend_url}/api", timeout=30.0) as primary_client:
        primary_login = primary_client.post("/admin/login", json={"username": PRIMARY_USERNAME, "password": PRIMARY_PASSWORD})
        assert primary_login.status_code == 200, primary_login.text
        listing = primary_client.get("/admin/admins")
        assert listing.status_code == 200, listing.text
        usernames = [row["username"] for row in listing.json()]
        assert PRIMARY_USERNAME in usernames
        assert SECONDARY_USERNAME in usernames


def test_admin_creation_endpoint_rejects_unauthenticated_request(backend_url):
    with httpx.Client(base_url=f"{backend_url}/api", timeout=30.0) as anon_client:
        response = anon_client.post(
            "/admin/admins",
            json={"name": "Tscheck Rogue Admin", "email": "tscheck-rogue@example.com", "username": "tscheck-rogue", "password": "RogueAdmin2026!"},
        )
    assert response.status_code in (401, 403), response.text
