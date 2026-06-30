"""Tests for scraper.py pure functions.

These tests do not hit the network.
"""

import pytest
import sys
from pathlib import Path

# Ensure we can import when running from backend/ or root
sys.path.insert(0, str(Path(__file__).parent.parent))
from scraper import extract_video_id


@pytest.mark.parametrize(
    "url, expected_id",
    [
        ("https://www.youtube.com/watch?v=dQw4w9wg3k", "dQw4w9wg3k"),
        ("https://youtu.be/dQw4w9wg3k", "dQw4w9wg3k"),
        ("https://www.youtube.com/shorts/abc123xyz", "abc123xyz"),
        ("https://youtube.com/watch?v=shortid123&feature=share", "shortid123"),
        ("https://m.youtube.com/watch?v=mobile123", "mobile123"),
        ("https://youtu.be/veryLongIdHere?si=xxx", "veryLongIdHere"),
    ],
)
def test_extract_video_id_valid(url: str, expected_id: str):
    assert extract_video_id(url) == expected_id


def test_extract_video_id_invalid():
    with pytest.raises(ValueError, match="could not extract video id"):
        extract_video_id("https://example.com/not-a-youtube-url")


def test_extract_video_id_empty():
    with pytest.raises(ValueError):
        extract_video_id("")
