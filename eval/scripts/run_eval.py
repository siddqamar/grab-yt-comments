#!/usr/bin/env python
"""
Run evaluation against a gold JSONL file.

- Uses isolated eval cache DB
- Supports --force to re-classify (invalidate cache entries)
- Produces JSON + markdown reports in eval/results/
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = EVAL_ROOT.parent
BACKEND_DIR = REPO_ROOT / "backend"

# CRITICAL: set isolated DB *before* importing classifier
EVAL_CACHE = EVAL_ROOT / "data" / ".eval_cache.sqlite3"
os.environ["CLASSIFICATION_DB_PATH"] = str(EVAL_CACHE)

# Now safe to import
sys.path.insert(0, str(BACKEND_DIR))

from classifier import LABELS, classify_comment_detailed, invalidate_cache_for_texts  # type: ignore

# Local metrics
sys.path.insert(0, str(EVAL_ROOT))
from metrics import build_full_report, format_report_markdown  # type: ignore


def load_gold(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("text") and rec.get("gold_label"):
                items.append(rec)
        except Exception:
            pass
    return items


def save_json(obj: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate classifier on gold set")
    parser.add_argument("--gold", required=True, help="Path to gold.jsonl")
    parser.add_argument("--force", action="store_true", help="Clear cache for these texts and re-run LLM")
    parser.add_argument("--limit", type=int, default=0, help="Only evaluate first N items (for quick checks)")
    parser.add_argument(
        "--out-dir",
        default=str(EVAL_ROOT / "results"),
        help="Where to write reports",
    )
    args = parser.parse_args()

    gold_path = Path(args.gold)
    gold = load_gold(gold_path)
    if not gold:
        print(f"No valid gold items found in {gold_path}")
        sys.exit(1)

    if args.limit > 0:
        gold = gold[: args.limit]

    texts = [g["text"] for g in gold]
    print(f"Loaded {len(gold)} gold examples.")
    print(f"Using eval cache: {EVAL_CACHE}")
    print(f"Current MODEL (from env or default): {os.getenv('LOCAL_LLM_MODEL', 'LiquidAI/LFM2.5-350M-GGUF:Q4_K_M')}")

    if args.force:
        print("Forcing fresh classification (invalidating cache entries)...")
        invalidate_cache_for_texts(texts)

    results: list[dict[str, Any]] = []
    golds: list[str] = []
    preds: list[str] = []

    print("Classifying...")
    start = time.time()
    for i, rec in enumerate(gold):
        text = rec["text"]
        try:
            detail = classify_comment_detailed(text)
            pred = detail.get("label", "feedback")
            raw = detail.get("raw_response")
        except Exception as exc:
            print(f"  [{i+1}/{len(gold)}] ERROR: {exc}")
            pred = "feedback"
            raw = f"ERROR: {exc}"

        golds.append(rec["gold_label"])
        preds.append(pred)

        enriched = dict(rec)
        enriched["pred_label"] = pred
        enriched["raw"] = raw
        results.append(enriched)

        if (i + 1) % 10 == 0 or (i + 1) == len(gold):
            print(f"  {i+1}/{len(gold)} classified")

    dur = time.time() - start
    print(f"Classification done in {dur:.1f}s")

    # Build report
    model_name = os.getenv("LOCAL_LLM_MODEL", "unknown")
    report = build_full_report(golds, preds, list(LABELS), results, model_name=model_name)
    report["gold_file"] = str(gold_path)
    report["run_at"] = datetime.now(timezone.utc).isoformat()
    report["duration_seconds"] = round(dur, 1)
    report["force_refresh"] = bool(args.force)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out_dir)
    json_path = out_dir / f"eval-{ts}.json"
    md_path = out_dir / f"eval-{ts}.md"

    save_json(report, json_path)
    md_content = format_report_markdown(report)
    save_text(md_content, md_path)

    # Console summary
    print("\n" + "=" * 60)
    print(f"ACCURACY: {report['accuracy']:.4f}   MACRO_F1: {report['macro_f1']:.4f}")
    print(f"Reports written:\n  {json_path}\n  {md_path}")
    print("=" * 60)
    print("\nConfusion (top view):")
    print(report.get("confusion_table", ""))

    if report.get("most_confused"):
        print("\nMost confused pairs:")
        for g, p, c in report["most_confused"][:3]:
            print(f"  {g} → {p} ({c})")


if __name__ == "__main__":
    main()
