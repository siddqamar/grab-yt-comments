import hashlib
import json
import os
import re
import sqlite3
import string
import time
from typing import Any, Callable

import requests

session = requests.Session()

MODEL_NAME = os.getenv("LOCAL_LLM_MODEL", "LiquidAI/LFM2.5-350M-GGUF:Q4_K_M")
URL = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
DB_PATH = os.getenv("CLASSIFICATION_DB_PATH", ".classification_cache.sqlite3")
BATCH_SIZE = int(os.getenv("CLASSIFICATION_BATCH_SIZE", "12"))
REQUEST_TIMEOUT = int(os.getenv("CLASSIFICATION_REQUEST_TIMEOUT", "30"))
CLEAR_CACHE_ON_RUN = os.getenv("CLASSIFICATION_CLEAR_CACHE_ON_RUN", "").lower() in {
    "1",
    "true",
    "yes",
}

LABELS = ("Question", "Criticism", "Affirmation", "Other")
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
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_classification_label ON classification_cache(label)"
    )


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _comment_hash(comment: str) -> str:
    return hashlib.sha256(comment.strip().encode("utf-8")).hexdigest()


def _cache_key(comment: str) -> str:
    payload = json.dumps(
        {"model": MODEL_NAME, "comment": comment.strip()},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _upsert_comment(conn: sqlite3.Connection, comment: dict[str, Any]) -> None:
    text = str(comment.get("text", ""))
    now = int(time.time())
    conn.execute(
        """
        INSERT INTO comments (comment_hash, comment_text, comment_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(comment_hash) DO UPDATE SET
            comment_text = excluded.comment_text,
            comment_json = excluded.comment_json,
            updated_at = excluded.updated_at
        """,
        (
            _comment_hash(text),
            text,
            json.dumps(comment, ensure_ascii=False, sort_keys=True),
            now,
            now,
        ),
    )


def _get_cached_label(conn: sqlite3.Connection, comment: str) -> str | None:
    row = conn.execute(
        "SELECT label FROM classification_cache WHERE comment_hash = ? AND source != 'fallback'",
        (_cache_key(comment),),
    ).fetchone()
    if row and row["label"] in LABELS:
        return row["label"]
    return None


def _save_label(
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


def _has_question_intent(text: str) -> bool:
    if "?" in text:
        return True

    question_patterns = (
        r"^(what|why|how|when|where|who|which)\b",
        r"\b(can|could|would|will|do|does|did|is|are|should)\s+(you|i|we|this|that|it|there)\b",
        r"\bplease\s+(explain|show|make|cover|help|tell)\b",
        r"\b(tutorial|guide|example|examples|explain|explanation)\b",
    )
    return any(re.search(pattern, text) for pattern in question_patterns)


def _rule_based_label(comment: str) -> str | None:
    text = comment.lower().strip()
    if not text:
        return "Other"
    if _has_question_intent(text):
        return "Question"

    criticism_terms = (
        "this is wrong",
        "you are wrong",
        "does not work",
        "doesn't work",
        "dont work",
        "don't work",
        "didn't work",
        "not working",
        "completely broken",
        "waste of time",
        "i hate",
    )
    if any(term in text for term in criticism_terms):
        return "Criticism"

    affirmation_terms = (
        "thank you",
        "thanks",
        "very helpful",
        "super helpful",
        "great video",
        "awesome video",
        "excellent video",
        "i agree",
        "i love this",
        "this helped",
        "worked perfectly",
    )
    if any(term in text for term in affirmation_terms):
        return "Affirmation"

    if _looks_like_low_value_other(text):
        return "Other"

    return None


def _looks_like_low_value_other(text: str) -> bool:
    if re.fullmatch(r"[\W_]+", text):
        return True
    if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", text):
        return True
    words = re.findall(r"[a-z0-9]+", text)
    return len(words) <= 2 and text in {"first", "subscribed", "ok", "lol", "haha", "wow"}


def _build_batch_payload(batch: list[tuple[int, str]]) -> dict[str, Any]:
    comments = [{"id": index, "text": text} for index, text in batch]
    prompt = f"""
You are analyzing YouTube comments for creator and product decision-making.
Your job is to sort audience feedback into useful action buckets, not generic sentiment.

Classify each comment into exactly one label.

Allowed labels:
- Question: asks for information, help, clarification, a tutorial, or a future topic.
- Criticism: complains, disagrees, reports a problem, expresses confusion, or gives negative feedback.
- Affirmation: praises, thanks, agrees, supports, or says the content helped.
- Other: unrelated, spam, joke-only, timestamp-only, emoji-only, or none of the above.

Rules:
- Return valid JSON only.
- Use the exact numeric ids provided.
- Treat requests for more detail, tutorials, examples, setup help, or clarification as Question.
- Treat failures, objections, confusion, disagreement, missing details, or pain points as Criticism.
- Treat thanks, praise, agreement, encouragement, or success reports as Affirmation.
- Use Other only when the comment is not a question, criticism, or affirmation.
- If a comment mixes labels, choose this priority: Question, then Criticism, then Affirmation, then Other.
- Do not include explanations.

Examples:
- "Can you show a full deployment example?" -> Question
- "Great video, but can you explain the setup step?" -> Question
- "I am not fully convinced this works for small teams." -> Criticism
- "This part was confusing and missed the main issue." -> Criticism
- "Thank you, this finally made agents click for me." -> Affirmation
- "Loved the explanation, very helpful." -> Affirmation
- "Watching from Brazil" -> Other
- "10:42" -> Other

Return shape:
{{"classifications":[{{"id":0,"label":"Question"}}]}}

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
                    "Classify comments by the user's actionable intent. Return JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": max(96, len(batch) * 16),
        "stream": False,
    }


def _extract_json(raw_response: str) -> dict[str, Any]:
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _classify_batch(batch: list[tuple[int, str]]) -> tuple[dict[int, str], str]:
    response = session.post(URL, json=_build_batch_payload(batch), timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    raw_response = response.json()["choices"][0]["message"]["content"].strip()
    parsed = _extract_json(raw_response)
    if isinstance(parsed, dict):
        rows = parsed.get("classifications", [])
    elif isinstance(parsed, list):
        rows = parsed
    else:
        rows = []

    labels = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                index = int(row.get("id"))
            except (TypeError, ValueError):
                continue
            labels[index] = _normalize_label(str(row.get("label", "Other")))

    return labels, raw_response


def _chunks(items: list[tuple[int, str]], size: int) -> list[list[tuple[int, str]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _prepare_run(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM comments")
    if CLEAR_CACHE_ON_RUN:
        conn.execute("DELETE FROM classification_cache")


def classify_comment(comment: str) -> str:
    if not comment or not isinstance(comment, str):
        return "Other"

    with _connect() as conn:
        cached_label = _get_cached_label(conn, comment)
        if cached_label:
            return cached_label

        rule_label = _rule_based_label(comment)
        if rule_label:
            _save_label(conn, comment, rule_label, None, "rule")
            conn.commit()
            return rule_label

        try:
            labels, raw_response = _classify_batch([(0, comment)])
            label = labels.get(0, "Other")
            _save_label(conn, comment, label, raw_response, "llm")
            conn.commit()
            return label
        except Exception:
            return "Other"


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
    labels_by_index: dict[int, str] = {}
    pending: list[tuple[int, str]] = []

    with _connect() as conn:
        _prepare_run(conn)
        for index, comment in enumerate(classified):
            text = str(comment.get("text", ""))
            _upsert_comment(conn, comment)

            cached_label = _get_cached_label(conn, text)
            if cached_label:
                labels_by_index[index] = cached_label
                continue

            rule_label = _rule_based_label(text)
            if rule_label:
                labels_by_index[index] = rule_label
                _save_label(conn, text, rule_label, None, "rule")
                continue

            pending.append((index, text))

        conn.commit()

        done = len(labels_by_index)
        if progress_callback:
            progress_callback(done, total, f"Resolved {done}/{total} comments from cache/rules")
        print(f"Classification: {done}/{total} resolved from cache/rules; {len(pending)} sent to LLM")

        for batch_number, batch in enumerate(_chunks(pending, max(1, BATCH_SIZE)), start=1):
            batch_start = time.time()
            try:
                batch_labels, raw_response = _classify_batch(batch)
                source = "llm_batch"
            except Exception as exc:
                batch_labels = {}
                raw_response = f"Batch classification failed: {exc}"
                source = "fallback"

            for index, text in batch:
                label = batch_labels.get(index) or _rule_based_label(text) or "Other"
                labels_by_index[index] = label
                _save_label(conn, text, label, raw_response, source)

            conn.commit()
            done = len(labels_by_index)
            elapsed = time.time() - batch_start
            message = f"Classified {done}/{total} comments"
            if progress_callback:
                progress_callback(done, total, message)
            print(f"{message} after batch {batch_number} ({elapsed:.2f}s)")

    for index, comment in enumerate(classified):
        comment["label"] = labels_by_index.get(index, "Other")

    return classified
