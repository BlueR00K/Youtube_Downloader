from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_info_bad_url():
    # Sending an obviously invalid URL should return a 400 or 422
    resp = client.post("/api/info", json={"url": "not-a-url"})
    assert resp.status_code >= 400


def test_download_bad_url():
    resp = client.post("/api/download", json={"url": "not-a-url"})
    assert resp.status_code >= 400
