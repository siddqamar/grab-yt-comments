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
