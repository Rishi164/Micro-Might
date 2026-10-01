def test_public_payment_qr_is_available(client):
    response = client.get("/payment-qr")
    assert response.status_code == 200
    payload = response.json()
    assert "qr_data_url" in payload
