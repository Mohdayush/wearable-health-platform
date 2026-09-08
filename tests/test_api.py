from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auth_device_and_dashboard_flow():
    email = "test-pulsepath@example.com"
    register = client.post("/api/v1/auth/register", json={"email": email, "name": "Test User", "password": "StrongPass123!"})
    assert register.status_code in (201, 409)
    token = register.json()["access_token"] if register.status_code == 201 else client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123!"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    device = client.post("/api/v1/devices", headers=headers, json={"name": "Test Band", "model": "PP-Test"})
    assert device.status_code == 201
    device_data = device.json()

    measurement = client.post(
        f"/api/v1/devices/{device_data['id']}/measurements",
        headers={"X-Device-Token": device_data["device_token"]},
        json={"metric": "heart_rate", "value": 72, "unit": "bpm", "observed_at": datetime.now(timezone.utc).isoformat(), "idempotency_key": "test-key-123456"},
    )
    assert measurement.status_code == 202

    dashboard = client.get("/api/v1/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert "heart_rate" in dashboard.json()["metrics"]

    assistant = client.post("/api/v1/assistant/chat", headers=headers, json={"message": "How is my heart rate?"})
    assert assistant.status_code == 200
    assert "heart-rate" in assistant.json()["answer"].lower()
