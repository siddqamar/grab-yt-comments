import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from classifier import LABELS, classify_comments
from scraper import extract_video_id, scrape_comments

load_dotenv()


class CommentRequest(BaseModel):
    url: str = Field(..., min_length=1)
    enable_classification: bool = False


def _allowed_origins() -> list[str]:
    configured = os.getenv("FRONTEND_ORIGINS", "")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


app = FastAPI(title="Grab YT Comments API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _frontend_comment(comment: dict[str, Any], index: int) -> dict[str, Any]:
    label = comment.get("label")
    return {
        "id": str(comment.get("comment_id") or f"comment-{index}"),
        "author": str(comment.get("author") or "Unknown"),
        "text": str(comment.get("text") or ""),
        "timestamp": str(comment.get("published_at") or ""),
        "likes": int(comment.get("like_count") or 0),
        "classification": str(label) if label else None,
    }


def _stats(comments: list[dict[str, Any]]) -> dict[str, int]:
    stats = {label: 0 for label in LABELS}
    for comment in comments:
        label = comment.get("label")
        if label in stats:
            stats[label] += 1
    stats["total"] = len(comments)
    return stats


@app.post("/api/v1/comments")
def get_comments(payload: CommentRequest) -> dict[str, Any]:
    url = payload.url.strip()

    try:
        extract_video_id(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid YouTube URL: {exc}") from exc

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="YOUTUBE_API_KEY environment variable not set")

    try:
        title, comments = scrape_comments(api_key, url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid YouTube URL: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error scraping comments: {exc}") from exc

    if payload.enable_classification:
        try:
            comments = classify_comments(comments)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Error during classification: {exc}") from exc

    return {
        "status": "success",
        "data": {
            "comments": [_frontend_comment(comment, index) for index, comment in enumerate(comments)],
            "stats": _stats(comments),
            "video_title": title,
            "video_url": url,
        },
    }
