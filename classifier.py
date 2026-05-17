import hashlib
import json
import os
import sqlite3
import string
import time
from typing import Any

import requests

session = requests.Session()

MODEL_NAME = os.getenv("LOCAL_LLM_MODEL", "LiquidAI/LFM2.5-350M-GGUF:Q4_K_M")
URL = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
DB_PATH = os.getenv("CLASSIFICATION_DB_PATH", ".classification_cache.sqlite3")

LABELS = ("Question", "Criticism", "Affirmation", "Other")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS classification_cache (
            comment_hash TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            label TEXT NOT NULL,
            raw_response TEXT,
            created_at INTEGER NOT NULL
        )
        """
    )
    return conn


def _cache_key(comment: str) -> str:
    payload = json.dumps(
        {"model": MODEL_NAME, "comment": comment.strip()},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _get_cached_label(comment: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT label FROM classification_cache WHERE comment_hash = ?",
            (_cache_key(comment),),
        ).fetchone()
    if row and row[0] in LABELS:
        return row[0]
    return None


def _save_cached_label(comment: str, label: str, raw_response: str | None) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO classification_cache (
                comment_hash, model_name, comment_text, label, raw_response, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (_cache_key(comment), MODEL_NAME, comment, label, raw_response, int(time.time())),
        )


def _normalize_label(raw_label: str) -> str:
    cleaned = raw_label.strip().strip(string.punctuation + "\"'`").lower()
    words = set(cleaned.replace("-", " ").replace("_", " ").split())

    if cleaned == "question" or "question" in words:
        return "Question"
    if cleaned == "criticism" or "criticism" in words or "critique" in words:
        return "Criticism"
    if cleaned in {"complaint", "negative"} or words.intersection({"complaint", "negative"}):
        return "Criticism"
    if cleaned in {"affirmation", "affirmative", "positive", "praise"}:
        return "Affirmation"
    if words.intersection({"affirmation", "affirmative", "positive", "praise", "thanks"}):
        return "Affirmation"
    if cleaned == "other" or "other" in words or "neutral" in words:
        return "Other"
    return "Other"


def _rule_based_fallback(comment: str) -> str:
    text = comment.lower()
    if "?" in text or text.startswith(("what ", "why ", "how ", "when ", "where ", "can ", "could ", "would ")):
        return "Question"

    criticism_terms = (
        "bad",
        "bug",
        "broken",
        "confusing",
        "does not work",
        "doesn't work",
        "dont work",
        "don't work",
        "didn't work",
        "can't",
        "cannot",
        "hate",
        "issue",
        "problem",
        "wrong",
        "worse",
    )
    if any(term in text for term in criticism_terms):
        return "Criticism"

    affirmation_terms = (
        "agree",
        "awesome",
        "excellent",
        "good",
        "great",
        "helpful",
        "love",
        "nice",
        "perfect",
        "thanks",
        "thank you",
    )
    if any(term in text for term in affirmation_terms):
        return "Affirmation"

    return "Other"


def _build_payload(comment: str) -> dict[str, Any]:
    prompt = f"""
Classify this YouTube comment into exactly one label:

Question - asks for information, help, clarification, a tutorial, or a future topic.
Criticism - complains, disagrees, reports a problem, expresses confusion, or gives negative feedback.
Affirmation - praises, thanks, agrees, supports, or says the content helped.
Other - unrelated, spam, joke-only, timestamp-only, emoji-only, or none of the above.

Rules:
- Return exactly one label from: Question, Criticism, Affirmation, Other.
- Use Other only when the comment is not a question, criticism, or affirmation.
- Do not explain your answer.

Comment: {comment}
""".strip()

    return {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict YouTube comment classifier. Return one label only.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 8,
        "stream": False,
    }


def classify_comment(comment: str) -> str:
    if not comment or not isinstance(comment, str):
        return "Other"

    cached_label = _get_cached_label(comment)
    if cached_label:
        return cached_label

    raw_response = None
    should_cache = True
    try:
        response = session.post(URL, json=_build_payload(comment), timeout=20)
        response.raise_for_status()

        result = response.json()
        raw_response = result["choices"][0]["message"]["content"].strip()
        label = _normalize_label(raw_response)

        if label == "Other":
            label = _rule_based_fallback(comment)

    except Exception as exc:
        raw_response = f"Classification request failed: {exc}"
        label = _rule_based_fallback(comment)
        should_cache = False

    if should_cache:
        _save_cached_label(comment, label, raw_response)
    return label


def classify_comments(comments: list[dict[str, Any]] | dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(comments, dict):
        comment_items = comments.get("comments", [])
    else:
        comment_items = comments

    if not isinstance(comment_items, list):
        raise ValueError("Classifier expected a list of comment dictionaries")

    classified = []
    for item in comment_items:
        if not isinstance(item, dict):
            continue

        comment = dict(item)
        comment["label"] = classify_comment(str(comment.get("text", "")))
        classified.append(comment)

    return classified
