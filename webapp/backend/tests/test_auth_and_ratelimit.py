import time
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_key_enforced(monkeypatch):
    # set API_KEY and ensure requests without header are rejected
    monkeypatch.setenv("API_KEY", "secret123")
    # stub out get_info so we don't call yt-dlp

    def _fake_info(url):
        return {
            "title": "fake",
            "id": "123",
            "uploader": "me",
            "duration": 10,
            "thumbnails": [],
            "formats": [],
        }

    monkeypatch.setattr("app.main.get_info", _fake_info)

    resp = client.post("/api/info", json={"url": "not-a-url"})
    # 401 because API key required
    assert resp.status_code == 401

    # with correct header, it proceeds and returns our fake info -> 200
    resp2 = client.post(
        "/api/info", json={"url": "not-a-url"}, headers={"X-API-KEY": "secret123"}
    )
    assert resp2.status_code == 200


def test_rate_limit(monkeypatch):
    # set low rate limit for test
    monkeypatch.setenv("RATE_LIMIT", "2")
    monkeypatch.setenv("RATE_PERIOD", "3")

    # ensure no API key required for this test
    monkeypatch.delenv("API_KEY", raising=False)

    # reset limiter state and stub out get_info so we don't call yt-dlp
    from app.ratelimit import rate_limiter
    rate_limiter.buckets.clear()

    # stub out get_info so we don't call yt-dlp
    def _fake_info(url):
        return {
            "title": "fake",
            "id": "123",
            "uploader": "me",
            "duration": 10,
            "thumbnails": [],
            "formats": [],
        }

    monkeypatch.setattr("app.main.get_info", _fake_info)

    # two quick requests should be allowed (200)
    r1 = client.post(
        "/api/info", json={"url": "https://example.com/watch?v=1"})
    r2 = client.post(
        "/api/info", json={"url": "https://example.com/watch?v=1"})
    assert r1.status_code == 200 and r2.status_code == 200

    # third should be rate limited (429)
    r3 = client.post(
        "/api/info", json={"url": "https://example.com/watch?v=1"})
    assert r3.status_code == 429

    # after waiting period, should work again
    time.sleep(3.1)
    r4 = client.post(
        "/api/info", json={"url": "https://example.com/watch?v=1"})
    assert r4.status_code == 200
