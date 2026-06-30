import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from typing import Any, Callable

import requests

session = requests.Session()
model_request_lock = threading.Lock()

MODEL_NAME = os.getenv("LOCAL_LLM_MODEL", "LiquidAI/LFM2.5-350M-GGUF:Q4_K_M")
URL = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
DB_PATH = os.getenv("CLASSIFICATION_DB_PATH", ".classification_cache.sqlite3")
REQUEST_TIMEOUT = int(os.getenv("CLASSIFICATION_REQUEST_TIMEOUT", "30"))
CLASSIFICATION_BATCH_SIZE = max(
    1,
    min(15, int(os.getenv("CLASSIFICATION_BATCH_SIZE", "12"))),
)
CLASSIFICATION_MAX_RETRIES = max(1, int(os.getenv("CLASSIFICATION_MAX_RETRIES", "3")))
CLASSIFICATION_BATCH_PAUSE = float(os.getenv("CLASSIFICATION_BATCH_PAUSE", "0.25"))

LABELS = (
    "appreciation",
    "humor",
    "questions",
    "criticism",
    "personal experience",
    "feedback",
    "spam",
)
ProgressCallback = Callable[[int, int, str], None]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            comment_hash TEXT PRIMARY KEY,
            comment_text TEXT NOT NULL,
            comment_json TEXT NOT NULL,
            run_index INTEGER,
            label TEXT,
            raw_response TEXT,
            classification_source TEXT,
            model_name TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """
    )
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
    _ensure_column(conn, "classification_cache", "source", "TEXT DEFAULT 'llm'")
    _ensure_column(conn, "classification_cache", "updated_at", "INTEGER")
    _ensure_column(conn, "comments", "run_index", "INTEGER")
    _ensure_column(conn, "comments", "label", "TEXT")
    _ensure_column(conn, "comments", "raw_response", "TEXT")
    _ensure_column(conn, "comments", "classification_source", "TEXT")
    _ensure_column(conn, "comments", "model_name", "TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_classification_label ON classification_cache(label)"
    )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _comment_row_hash(comment: str, run_index: int) -> str:
    return hashlib.sha256(f"{run_index}:{comment.strip()}".encode("utf-8")).hexdigest()


def _cache_key(comment: str) -> str:
    payload = json.dumps(
        {"model": MODEL_NAME, "comment": comment.strip()},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _upsert_comment(conn: sqlite3.Connection, comment: dict[str, Any], run_index: int = 0) -> None:
    text = str(comment.get("text", ""))
    now = int(time.time())
    conn.execute(
        """
        INSERT INTO comments (
            comment_hash, comment_text, comment_json, run_index, label,
            raw_response, classification_source, model_name, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?)
        ON CONFLICT(comment_hash) DO UPDATE SET
            comment_text = excluded.comment_text,
            comment_json = excluded.comment_json,
            run_index = excluded.run_index,
            label = NULL,
            raw_response = NULL,
            classification_source = NULL,
            model_name = excluded.model_name,
            updated_at = excluded.updated_at
        """,
        (
            _comment_row_hash(text, run_index),
            text,
            json.dumps(comment, ensure_ascii=False, sort_keys=True),
            run_index,
            MODEL_NAME,
            now,
            now,
        ),
    )


def _save_cached_label(
    conn: sqlite3.Connection,
    comment: str,
    label: str,
    raw_response: str | None,
    source: str,
) -> None:
    now = int(time.time())
    conn.execute(
        """
        INSERT INTO classification_cache (
            comment_hash, model_name, comment_text, label, raw_response, created_at, source, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(comment_hash) DO UPDATE SET
            model_name = excluded.model_name,
            comment_text = excluded.comment_text,
            label = excluded.label,
            raw_response = excluded.raw_response,
            source = excluded.source,
            updated_at = excluded.updated_at
        """,
        (_cache_key(comment), MODEL_NAME, comment, label, raw_response, now, source, now),
    )


def _get_cached_label(conn: sqlite3.Connection, comment: str) -> tuple[str, str | None] | None:
    row = conn.execute(
        """
        SELECT label, raw_response
        FROM classification_cache
        WHERE comment_hash = ?
        """,
        (_cache_key(comment),),
    ).fetchone()
    if not row:
        return None
    return _normalize_label(str(row["label"])), row["raw_response"]


def _save_comment_label(
    conn: sqlite3.Connection,
    comment_hash: str,
    label: str,
    raw_response: str | None,
    source: str,
) -> None:
    now = int(time.time())
    conn.execute(
        """
        UPDATE comments
        SET label = ?,
            raw_response = ?,
            classification_source = ?,
            model_name = ?,
            updated_at = ?
        WHERE comment_hash = ?
        """,
        (label, raw_response, source, MODEL_NAME, now, comment_hash),
    )


def _normalize_label(raw_label: str) -> str:
    cleaned = raw_label.strip().strip(".,:;!?\"'`[]{}()").lower()
    cleaned = re.sub(r"\s+", " ", cleaned.replace("-", " ").replace("_", " "))
    if cleaned in LABELS:
        return cleaned

    aliases = {
        "appreciation": "appreciation",
        "praise": "appreciation",
        "thanks": "appreciation",
        "thank you": "appreciation",
        "positive": "appreciation",
        "humor": "humor",
        "humour": "humor",
        "joke": "humor",
        "funny": "humor",
        "question": "questions",
        "questions": "questions",
        "criticism": "criticism",
        "critique": "criticism",
        "complaint": "criticism",
        "negative": "criticism",
        "personal experience": "personal experience",
        "experience": "personal experience",
        "story": "personal experience",
        "feedback": "feedback",
        "suggestion": "feedback",
        "feature request": "feedback",
        "spam": "spam",
        "scam": "spam",
        "bot": "spam",
    }
    return aliases.get(cleaned, "feedback")


def _build_comment_payload(comment_text: str) -> dict[str, Any]:
    prompt = f"""
You are analyzing YouTube comments for creator and product decision-making.
Your job is to sort one audience comment into one useful action bucket.

Classify the comment into exactly one label.

Allowed labels:
- appreciation: praise, thanks, agreement, encouragement, or saying the content helped.
- humor: jokes, memes, playful remarks, or light sarcasm meant mainly to entertain.
- questions: asks for information, help, clarification, a tutorial, an example, or a future topic.
- criticism: complains, disagrees, reports a problem, expresses confusion, or gives negative judgment.
- personal experience: shares a first-person story, outcome, use case, or lived experience.
- feedback: gives a suggestion, feature request, constructive advice, or improvement idea.
- spam: clear scam, bot text, unrelated promotion, repeated junk, suspicious link, fake giveaway, or self-promotion.

Return shape:
{{"label":"questions"}}

Comment:
{json.dumps(comment_text, ensure_ascii=False)}
""".strip()

    return {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior audience-insights analyst for YouTube creators and product teams. "
                    "Classify exactly one comment by the user's actionable intent. Return JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 32,
        "stream": False,
    }


def _build_batch_payload(comment_texts: list[str]) -> dict[str, Any]:
    comments = [
        {"id": f"c{index}", "text": text}
        for index, text in enumerate(comment_texts)
    ]
    prompt = f"""
You are analyzing YouTube comments for creator and product decision-making.
Your job is to sort each audience comment into one useful action bucket.

Classify every comment into exactly one label.

Allowed labels:
- appreciation: praise, thanks, agreement, encouragement, or saying the content helped.
- humor: jokes, memes, playful remarks, or light sarcasm meant mainly to entertain.
- questions: asks for information, help, clarification, a tutorial, an example, or a future topic.
- criticism: complains, disagrees, reports a problem, expresses confusion, or gives negative judgment.
- personal experience: shares a first-person story, outcome, use case, or lived experience.
- feedback: gives a suggestion, feature request, constructive advice, or improvement idea.
- spam: clear scam, bot text, unrelated promotion, repeated junk, suspicious link, fake giveaway, or self-promotion.

Return valid JSON only.
Return one result for every input comment using the exact same id.
Do not include explanations.

Return shape:
{{"results":[{{"id":"c0","label":"questions"}}]}}

Comments:
{json.dumps(comments, ensure_ascii=False)}
""".strip()

    return {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior audience-insights analyst for YouTube creators and product teams. "
                    "Classify batches of comments by actionable intent. Return JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": max(96, 32 * len(comment_texts)),
        "stream": False,
    }


def _extract_json(raw_response: str) -> Any:
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _post_with_retries(payload: dict[str, Any]) -> requests.Response:
    retry_statuses = {429, 500, 502, 503, 504}
    last_error: Exception | None = None

    for attempt in range(CLASSIFICATION_MAX_RETRIES):
        try:
            with model_request_lock:
                response = session.post(URL, json=payload, timeout=REQUEST_TIMEOUT)
            if response.status_code not in retry_statuses:
                response.raise_for_status()
                return response

            response.raise_for_status()
        except requests.RequestException as exc:
            last_error = exc
            if attempt == CLASSIFICATION_MAX_RETRIES - 1:
                break
            time.sleep((1.5 ** attempt) + (attempt * 0.25))

    if last_error:
        raise last_error
    raise RuntimeError("Classification request failed")


def _classify_one(comment_text: str) -> tuple[str, str]:
    response = _post_with_retries(_build_comment_payload(comment_text))

    raw_response = response.json()["choices"][0]["message"]["content"].strip()
    parsed = _extract_json(raw_response)
    if isinstance(parsed, dict):
        return _normalize_label(str(parsed.get("label", "feedback"))), raw_response
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        return _normalize_label(str(parsed[0].get("label", "feedback"))), raw_response
    return "feedback", raw_response


def _extract_batch_labels(parsed: Any, expected_ids: list[str]) -> list[str]:
    items: Any
    if isinstance(parsed, dict):
        items = (
            parsed.get("results")
            or parsed.get("comments")
            or parsed.get("classifications")
            or parsed.get("labels")
        )
    else:
        items = parsed

    labels_by_id: dict[str, str] = {}
    positional_labels: list[str] = []

    if isinstance(items, dict):
        for comment_id, label in items.items():
            labels_by_id[str(comment_id)] = _normalize_label(str(label))
    elif isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                label = item.get("label") or item.get("classification") or item.get("category")
                comment_id = item.get("id") or item.get("comment_id")
                if comment_id is not None and label is not None:
                    labels_by_id[str(comment_id)] = _normalize_label(str(label))
                elif label is not None:
                    positional_labels.append(_normalize_label(str(label)))
            elif isinstance(item, str):
                positional_labels.append(_normalize_label(item))

    labels: list[str] = []
    for index, comment_id in enumerate(expected_ids):
        if comment_id in labels_by_id:
            labels.append(labels_by_id[comment_id])
        elif index < len(positional_labels):
            labels.append(positional_labels[index])
        else:
            labels.append("feedback")
    return labels


def _classify_batch(comment_texts: list[str]) -> list[tuple[str, str]]:
    if not comment_texts:
        return []
    if len(comment_texts) == 1:
        return [_classify_one(comment_texts[0])]

    response = _post_with_retries(_build_batch_payload(comment_texts))
    raw_response = response.json()["choices"][0]["message"]["content"].strip()
    parsed = _extract_json(raw_response)
    expected_ids = [f"c{index}" for index in range(len(comment_texts))]
    labels = _extract_batch_labels(parsed, expected_ids)
    return [(label, raw_response) for label in labels]


def _classify_batch_resilient(comment_texts: list[str]) -> list[tuple[str, str]]:
    try:
        return _classify_batch(comment_texts)
    except Exception:
        if len(comment_texts) <= 1:
            raise

        midpoint = len(comment_texts) // 2
        return (
            _classify_batch_resilient(comment_texts[:midpoint])
            + _classify_batch_resilient(comment_texts[midpoint:])
        )


def _chunk(items: list[sqlite3.Row], size: int) -> list[list[sqlite3.Row]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def _prepare_run(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM comments")


def _load_classified_comments(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT comment_json, label
        FROM comments
        ORDER BY run_index ASC, updated_at ASC
        """
    ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        try:
            comment = json.loads(row["comment_json"])
        except json.JSONDecodeError:
            comment = {"text": ""}
        if isinstance(comment, dict):
            comment["label"] = row["label"] or "feedback"
            results.append(comment)
    return results


def compute_cache_key(comment: str) -> str:
    """Public helper: deterministic cache key for a comment + current model.
    Useful for external tools (e.g. eval) that need to manage cache entries.
    """
    payload = json.dumps(
        {"model": MODEL_NAME, "comment": comment.strip()},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def invalidate_cache_for_texts(texts: list[str]) -> None:
    """Remove cached classifications for the given texts (current MODEL_NAME).
    Safe no-op if texts are empty. Intended primarily for evaluation runs.
    """
    if not texts:
        return
    with _connect() as conn:
        keys = [compute_cache_key(t) for t in texts if t]
        if not keys:
            return
        placeholders = ",".join("?" for _ in keys)
        conn.execute(
            f"DELETE FROM classification_cache WHERE comment_hash IN ({placeholders})",
            keys,
        )
        conn.commit()


def classify_comment(comment: str) -> str:
    if not comment or not isinstance(comment, str):
        return "feedback"

    with _connect() as conn:
        cached = _get_cached_label(conn, comment)
        if cached:
            return cached[0]

        label, raw_response = _classify_one(comment)
        _save_cached_label(conn, comment, label, raw_response, "llm")
        conn.commit()
        return label


def classify_comment_detailed(comment: str) -> dict[str, Any]:
    """Classify a single comment and return richer result including raw LLM response.

    Returns: {"label": str, "raw_response": str | None, "source": "llm" | "cache"}
    This is additive and does not change behavior of classify_comment().
    """
    if not comment or not isinstance(comment, str):
        return {"label": "feedback", "raw_response": None, "source": "none"}

    with _connect() as conn:
        cached = _get_cached_label(conn, comment)
        if cached:
            label, raw = cached
            return {"label": label, "raw_response": raw, "source": "cache"}

        label, raw_response = _classify_one(comment)
        _save_cached_label(conn, comment, label, raw_response, "llm")
        conn.commit()
        return {"label": label, "raw_response": raw_response, "source": "llm"}


def classify_comments(
    comments: list[dict[str, Any]] | dict[str, Any],
    progress_callback: ProgressCallback | None = None,
) -> list[dict[str, Any]]:
    if isinstance(comments, dict):
        comment_items = comments.get("comments", [])
    else:
        comment_items = comments

    if not isinstance(comment_items, list):
        raise ValueError("Classifier expected a list of comment dictionaries")

    classified = [dict(item) for item in comment_items if isinstance(item, dict)]
    total = len(classified)

    with _connect() as conn:
        _prepare_run(conn)
        for index, comment in enumerate(classified):
            _upsert_comment(conn, comment, index)

        conn.commit()

        if progress_callback:
            progress_callback(0, total, f"Stored {total} comments before classification")

        rows = conn.execute(
            """
            SELECT comment_hash, comment_text
            FROM comments
            ORDER BY run_index ASC
            """
        ).fetchall()

        queued_rows: list[sqlite3.Row] = []
        done = 0

        for row in rows:
            text = str(row["comment_text"])
            cached = _get_cached_label(conn, text)
            if not cached:
                queued_rows.append(row)
                continue

            label, raw_response = cached
            _save_comment_label(conn, row["comment_hash"], label, raw_response, "cache")
            done += 1
            message = f"Loaded cached classification {done}/{total} comments"
            if progress_callback:
                progress_callback(done, total, message)

        conn.commit()

        if queued_rows and progress_callback:
            progress_callback(done, total, f"Queued {len(queued_rows)} uncached comments for batch classification")

        for batch in _chunk(queued_rows, CLASSIFICATION_BATCH_SIZE):
            texts = [str(row["comment_text"]) for row in batch]
            batch_results = _classify_batch_resilient(texts)

            for row, text, result in zip(batch, texts, batch_results):
                label, raw_response = result
                _save_comment_label(conn, row["comment_hash"], label, raw_response, "llm")
                _save_cached_label(conn, text, label, raw_response, "llm")
                done += 1

            conn.commit()
            if CLASSIFICATION_BATCH_PAUSE > 0:
                time.sleep(CLASSIFICATION_BATCH_PAUSE)

            message = f"Classified {done}/{total} comments"
            if progress_callback:
                progress_callback(done, total, message)
            print(message)

        return _load_classified_comments(conn)
