#!/usr/bin/env python
"""
Interactive CLI labeler for gold dataset creation / extension.

Resumes automatically. Forgiving input (numbers, names, aliases).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _make_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = EVAL_ROOT.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

try:
    from classifier import LABELS  # type: ignore
except Exception:
    LABELS = (
        "appreciation",
        "humor",
        "questions",
        "criticism",
        "personal experience",
        "feedback",
        "spam",
    )

# Simple forgiving aliases (subset of classifier logic)
ALIASES = {
    "1": "appreciation",
    "a": "appreciation",
    "app": "appreciation",
    "praise": "appreciation",
    "2": "humor",
    "h": "humor",
    "hum": "humor",
    "funny": "humor",
    "joke": "humor",
    "3": "questions",
    "q": "questions",
    "que": "questions",
    "ask": "questions",
    "4": "criticism",
    "c": "criticism",
    "crit": "criticism",
    "neg": "criticism",
    "5": "personal experience",
    "p": "personal experience",
    "pe": "personal experience",
    "story": "personal experience",
    "exp": "personal experience",
    "6": "feedback",
    "f": "feedback",
    "fb": "feedback",
    "sug": "feedback",
    "7": "spam",
    "s": "spam",
    "sp": "spam",
    "bot": "spam",
}


def normalize_label(raw: str) -> str | None:
    cleaned = raw.strip().lower()
    if cleaned in LABELS:
        return cleaned
    return ALIASES.get(cleaned)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return items


def append_jsonl(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive gold labeler")
    parser.add_argument(
        "--candidates", required=True, help="Path to candidates.jsonl"
    )
    parser.add_argument(
        "--gold", default=str(EVAL_ROOT / "data" / "gold.jsonl"), help="Gold output JSONL"
    )
    args = parser.parse_args()

    cand_path = Path(args.candidates)
    gold_path = Path(args.gold)

    candidates = load_jsonl(cand_path)
    if not candidates:
        print(f"No candidates in {cand_path}")
        sys.exit(1)

    gold = load_jsonl(gold_path)
    already_labeled = {g.get("text") for g in gold if g.get("text")}

    remaining = [c for c in candidates if c.get("text") not in already_labeled]
    print(f"Gold already has {len(already_labeled)} labels.")
    print(f"Remaining to label: {len(remaining)}")

    label_menu = "  ".join(f"{i+1}={lab}" for i, lab in enumerate(LABELS))
    print(f"\nLabels: {label_menu}")
    print("Input: number, short name, or full label. 's' skip, 'q' quit, 'full' to show full text.\n")

    for idx, cand in enumerate(remaining):
        text = cand.get("text", "")
        src = cand.get("source", "?")
        print(f"\n[{idx+1}/{len(remaining)}] source={src}")
        print("---")
        display = text if len(text) < 420 else text[:400] + " ... (truncated)"
        print(display)
        print("---")

        while True:
            choice = input("label> ").strip()
            if not choice:
                continue
            if choice.lower() == "q":
                print("Quitting. Progress saved.")
                return
            if choice.lower() == "s":
                print("Skipped.")
                break
            if choice.lower() == "full":
                print(text)
                continue

            lab = normalize_label(choice)
            if lab is None:
                print(f"Unknown label '{choice}'. Try one of: {', '.join(LABELS)} or numbers 1-7")
                continue

            record = {
                "id": cand.get("id") or _make_id(text),
                "text": text,
                "gold_label": lab,
                "source": src,
                "labeled_at": datetime.now(timezone.utc).isoformat(),
                "labeler_notes": "",
            }
            # Try to carry over any extra fields from candidate
            for k in ("video_hint", "length"):
                if k in cand:
                    record[k] = cand[k]

            append_jsonl(record, gold_path)
            print(f"Saved as: {lab}")
            break

    print(f"\nDone. Gold now has {len(load_jsonl(gold_path))} labeled items.")


if __name__ == "__main__":
    main()
