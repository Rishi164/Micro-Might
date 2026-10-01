"""Criterion: Admin stock management uses real pack counts (and G.Y.O.C. stays made to order).

Uses a dedicated catalog slug (vital-seed) not touched by other tests to avoid cross-test
interference with shared inventory state. Sets a real pack count with enforcement enabled,
asserts over-ordering is blocked, a confirmed regular order deducts the matching pack count,
and a confirmed G.Y.O.C. order on the same slug does NOT deduct regular stock. Restores the
inventory row to untracked/zero afterwards so other runs see the documented default.
"""

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "micromight2026"
SLUG = "vital-seed"


def _login_admin(client):
    admin_login = client.post("/admin/login", json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert admin_login.status_code == 200, admin_login.text


def _order_payload(plan: str, phone: str, quantity: int = 1):
    return {
        "customer_name": "Tscheck Stock Order",
        "customer_email": "delivered@resend.dev",
        "customer_phone": phone,
        "delivery_address": "5 Tscheck Stock Lane, Gottigere",
        "pincode": "560083",
        "estimated_distance_km": 2,
        "preferred_delivery_date": "2026-12-27",
        "payment_method": "cod",
        "payment_reference": None,
        "notes": None,
        "items": [{"product_slug": SLUG, "plan": plan, "weight": "50g", "quantity": quantity}],
    }


def test_stock_enforcement_blocks_overorder_and_deducts_on_confirm(client):
    _login_admin(client)
    try:
        # Set real stock with enforcement enabled: 1 pack of 50g.
        set_stock = client.put(f"/admin/inventory/{SLUG}", json={
            "tracking_enabled": True,
            "stock_50g": 1,
            "stock_100g": 0,
        })
        assert set_stock.status_code == 200, set_stock.text
        assert set_stock.json()["tracking_enabled"] is True
        assert set_stock.json()["stock_50g"] == 1

        # Over-ordering (qty 2 against stock of 1) must be blocked at checkout.
        over_order = client.post("/orders", json=_order_payload("regular", "9900066111", quantity=2))
        assert over_order.status_code == 409, over_order.text

        # G.Y.O.C. remains made-to-order and is allowed even though regular stock is thin.
        gyoc_order = client.post("/orders", json=_order_payload("gyoc", "9900066222", quantity=5))
        assert gyoc_order.status_code == 201, gyoc_order.text
        gyoc_id = gyoc_order.json()["id"]
        confirm_gyoc = client.patch(f"/admin/orders/{gyoc_id}", json={
            "status": "confirmed",
            "approved_delivery_fee": 0,
            "approved_harvest_date": "2026-12-25",
            "approved_delivery_date": "2026-12-27",
        })
        assert confirm_gyoc.status_code == 200, confirm_gyoc.text

        # Regular stock must be untouched by the G.Y.O.C. confirmation.
        after_gyoc = client.get("/admin/inventory")
        row_after_gyoc = next(row for row in after_gyoc.json() if row["product_slug"] == SLUG)
        assert row_after_gyoc["stock_50g"] == 1

        # Valid regular order within stock (qty 1) succeeds and deducts on confirmation.
        ok_order = client.post("/orders", json=_order_payload("regular", "9900066333", quantity=1))
        assert ok_order.status_code == 201, ok_order.text
        ok_id = ok_order.json()["id"]
        confirm_ok = client.patch(f"/admin/orders/{ok_id}", json={
            "status": "confirmed",
            "approved_delivery_fee": 0,
            "approved_harvest_date": "2026-12-25",
            "approved_delivery_date": "2026-12-27",
        })
        assert confirm_ok.status_code == 200, confirm_ok.text

        after_confirm = client.get("/admin/inventory")
        row = next(row for row in after_confirm.json() if row["product_slug"] == SLUG)
        assert row["stock_50g"] == 0
    finally:
        # Restore documented default (untracked, zero) so other runs see no invented stock.
        client.put(f"/admin/inventory/{SLUG}", json={
            "tracking_enabled": False,
            "stock_50g": 0,
            "stock_100g": 0,
        })


def test_unauthenticated_inventory_update_rejected(backend_url):
    import httpx
    with httpx.Client(base_url=f"{backend_url}/api", timeout=30.0) as anon_client:
        response = anon_client.put(f"/admin/inventory/{SLUG}", json={
            "tracking_enabled": True,
            "stock_50g": 10,
            "stock_100g": 10,
        })
    assert response.status_code in (401, 403), response.text
