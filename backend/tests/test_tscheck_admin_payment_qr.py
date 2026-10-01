def test_payment_qr_update_rejects_unauthenticated_request(client):
    response = client.put(
        "/payment-qr",
        json={"qr_data_url": "data:image/png;base64,dHNjaGVjay1wYXltZW50LXFy"},
    )
    assert response.status_code in (401, 403), response.text


def test_payment_qr_update_accepts_admin_session(client):
    login = client.post("/admin/login", json={"username": "admin", "password": "micromight2026"})
    assert login.status_code == 200, login.text

    qr = "data:image/png;base64,dHNjaGVjay1wYXltZW50LXFy"
    response = client.put("/payment-qr", json={"qr_data_url": qr})
    assert response.status_code == 200, response.text
    assert response.json()["qr_data_url"] == qr

    reread = client.get("/payment-qr")
    assert reread.status_code == 200
    assert reread.json()["qr_data_url"] == qr
