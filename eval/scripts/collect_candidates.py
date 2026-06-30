#!/usr/bin/env python
"""
Collect candidate comments for human labeling.

Usage (from repo root):
    python eval/scripts/collect_candidates.py --sample 150 --out eval/data/candidates.jsonl

Can also read from backend/outputs/*.csv (fast, no API quota).
Future: support --from-urls using the scraper.
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

# Make backend importable when running from repo root or inside eval/
SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_ROOT = SCRIPT_DIR.parent
REPO_ROOT = EVAL_ROOT.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def normalize_for_dedup(text: str) -> str:
    return " ".join(text.lower().split())


def load_from_outputs(max_per_file: int = 200) -> list[dict[str, Any]]:
    """Load texts from existing backend/outputs/*.csv files."""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    output_dir = BACKEND_DIR / "outputs"
    csv_files = sorted(glob.glob(str(output_dir / "*_comments.csv")))

    for csv_path in csv_files:
        try:
            with open(csv_path, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    text = (row.get("text") or "").strip()
                    if not text or len(text) < 8:
                        continue
                    norm = normalize_for_dedup(text)
                    if norm in seen:
                        continue
                    seen.add(norm)

                    cid = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
                    candidates.append(
                        {
                            "id": cid,
                            "text": text,
                            "source": Path(csv_path).name,
                        }
                    )
                    count += 1
                    if count >= max_per_file:
                        break
        except Exception as exc:
            print(f"[warn] failed reading {csv_path}: {exc}")

    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect candidates for gold labeling")
    parser.add_argument("--sample", type=int, default=150, help="How many to output after shuffle")
    parser.add_argument(
        "--out",
        type=str,
        default=str(EVAL_ROOT / "data" / "candidates.jsonl"),
        help="Output JSONL path",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    print("Collecting candidates from backend/outputs/ ...")
    cands = load_from_outputs()

    if not cands:
        print("No candidates found. Make sure backend/outputs/*.csv exist.")
        sys.exit(1)

    print(f"Found {len(cands)} unique candidates after dedup.")

    random.seed(args.seed)
    random.shuffle(cands)

    sample = cands[: args.sample]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for c in sample:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Wrote {len(sample)} candidates → {out_path}")
    print("Next: python eval/scripts/interactive_label.py --candidates", out_path)


if __name__ == "__main__":
    main()
