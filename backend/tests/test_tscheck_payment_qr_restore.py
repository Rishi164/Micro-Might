"""Ensures the admin demo QR-replace flow can restore the supplied public PhonePe QR.

This mirrors the browser check `admin-replaces-payment-qr`, which temporarily sets a
fixture QR then restores the supplied zncy8do5_image.png QR via this same endpoint.
"""

SUPPLIED_QR_URL = (
    "https://customer-assets-4nw71qhi.emergentagent.net/"
    "job_fresh-from-trays/artifacts/zncy8do5_image.png"
)


def test_payment_qr_can_be_restored_to_supplied_phonepe_qr(client):
    fixture_qr = "data:image/png;base64,dHNjaGVjay1xci1yZXN0b3Jl"

    temp_response = client.put(
        "/payment-qr",
        json={
            "qr_data_url": fixture_qr,
            "admin_username": "admin",
            "admin_password": "micromight2026",
        },
    )
    assert temp_response.status_code == 200
    assert temp_response.json()["qr_data_url"] == fixture_qr

    restore_response = client.put(
        "/payment-qr",
        json={
            "qr_data_url": SUPPLIED_QR_URL,
            "admin_username": "admin",
            "admin_password": "micromight2026",
        },
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["qr_data_url"] == SUPPLIED_QR_URL

    reread = client.get("/payment-qr")
    assert reread.status_code == 200
    assert reread.json()["qr_data_url"] == SUPPLIED_QR_URL
