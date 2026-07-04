"""API tests using FastAPI TestClient.

These mock external dependencies (YouTube API + classifier).
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from api import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint_reports_missing_dependencies(monkeypatch, client):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.setattr(
        "api.get_model_readiness",
        lambda: {
            "available": False,
            "message": "Classification model server is unavailable.",
            "model": "test-model",
        },
    )

    response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["backend"]["available"] is True
    assert data["youtube"]["configured"] is False
    assert data["classification"]["available"] is False


def test_comments_invalid_url(client):
    """Test validation for bad YouTube URL."""
    response = client.post(
        "/api/v1/comments",
        json={"url": "https://not-a-youtube.com/video", "enable_classification": False},
    )
    assert response.status_code == 400
    assert "Invalid YouTube URL" in response.json()["detail"]


def test_comments_missing_api_key(monkeypatch, client):
    """If no YOUTUBE_API_KEY, should return 500."""
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    response = client.post(
        "/api/v1/comments",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9wg3k", "enable_classification": False},
    )
    assert response.status_code == 500
    assert "YOUTUBE_API_KEY" in response.json()["detail"]


def test_comments_success_no_classification(monkeypatch, client):
    """Happy path without classification."""
    # Patch the scraper to avoid real API call
    def fake_scrape(api_key, video_url):
        return "Test Video Title", [
            {"text": "Great video!", "published_at": "2024-01-01", "like_count": 10, "reply_count": 0},
            {"text": "Thanks!", "published_at": "2024-01-02", "like_count": 5, "reply_count": 1},
        ]

    monkeypatch.setenv("YOUTUBE_API_KEY", "fake-key")
    monkeypatch.setattr("api.scrape_comments", fake_scrape)

    response = client.post(
        "/api/v1/comments",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9wg3k", "enable_classification": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["video_title"] == "Test Video Title"
    assert len(data["data"]["comments"]) == 2
    assert data["data"]["stats"]["total"] == 2
    assert data["data"]["comments"][0]["classification"] is None


def test_comments_classification_unavailable_returns_scrape_only(monkeypatch, client):
    def fake_scrape(api_key, video_url):
        return "Test Video Title", [
            {"text": "Great video!", "published_at": "2024-01-01", "like_count": 10},
            {"text": "Thanks!", "published_at": "2024-01-02", "like_count": 5},
        ]

    def fail_if_classify(_comments):
        raise AssertionError("classify_comments should not run when the model is unavailable")

    monkeypatch.setenv("YOUTUBE_API_KEY", "fake-key")
    monkeypatch.setattr("api.scrape_comments", fake_scrape)
    monkeypatch.setattr(
        "api.get_model_readiness",
        lambda: {
            "available": False,
            "message": "Classification model server is unavailable.",
            "model": "test-model",
        },
    )
    monkeypatch.setattr("api.classify_comments", fail_if_classify)

    response = client.post(
        "/api/v1/comments",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9wg3k", "enable_classification": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["classification"]["requested"] is True
    assert data["meta"]["classification"]["applied"] is False
    assert data["meta"]["classification"]["status"] == "unavailable"
    assert data["data"]["stats"]["total"] == 2
    assert all(comment["classification"] is None for comment in data["data"]["comments"])


def test_comments_classification_failure_degrades_gracefully(monkeypatch, client):
    def fake_scrape(api_key, video_url):
        return "Test Video Title", [
            {"text": "Great video!", "published_at": "2024-01-01", "like_count": 10},
        ]

    monkeypatch.setenv("YOUTUBE_API_KEY", "fake-key")
    monkeypatch.setattr("api.scrape_comments", fake_scrape)
    monkeypatch.setattr(
        "api.get_model_readiness",
        lambda: {
            "available": True,
            "message": "Classification model server is reachable.",
            "model": "test-model",
        },
    )
    monkeypatch.setattr("api.classify_comments", lambda _comments: (_ for _ in ()).throw(RuntimeError("boom")))

    response = client.post(
        "/api/v1/comments",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9wg3k", "enable_classification": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["classification"]["status"] == "failed"
    assert data["meta"]["classification"]["applied"] is False
    assert data["data"]["stats"]["total"] == 1
