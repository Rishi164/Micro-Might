def test_payment_qr_update_rejects_invalid_credentials(client):
    response = client.put(
        "/payment-qr",
        json={
            "qr_data_url": "data:image/png;base64,dHNjaGVjay1wYXltZW50LXFy",
            "admin_username": "wrong",
            "admin_password": "wrong",
        },
    )
    assert response.status_code == 401
    assert "Invalid" in response.text


def test_payment_qr_update_accepts_demo_credentials(client):
    qr = "data:image/png;base64,dHNjaGVjay1wYXltZW50LXFy"
    response = client.put(
        "/payment-qr",
        json={
            "qr_data_url": qr,
            "admin_username": "admin",
            "admin_password": "micromight2026",
        },
    )
    assert response.status_code == 200
    assert response.json()["qr_data_url"] == qr

    reread = client.get("/payment-qr")
    assert reread.status_code == 200
    assert reread.json()["qr_data_url"] == qr
