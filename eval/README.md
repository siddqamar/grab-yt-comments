# Eval — YouTube Comment Classifier Evaluation

Dedicated tooling to measure, debug, and iteratively improve the local-LLM classification quality.

**No prior labels existed.** This folder provides everything needed to bootstrap a high-quality golden dataset and run repeatable evaluations.

## Why This Matters

The classifier uses a **very small model** (LiquidAI LFM2.5-350M). Prompt wording, JSON extraction, and the normalize step have a big impact. Evaluation gives you:
- Quantitative scores (accuracy, per-class F1)
- Qualitative error analysis (with raw model responses)
- A repeatable way to validate improvements

## Quick Start (PowerShell / Windows)

Prerequisites (same as the main app):
- Local LLM server running (`llama-server -hf LiquidAI/LFM2.5-350M-GGUF:Q4_K_M`)
- `YOUTUBE_API_KEY` only needed if you want to scrape fresh videos

From the **repo root**:

```powershell
# 1. Collect candidate comments from the already-scraped outputs (~1600 available)
python eval/scripts/collect_candidates.py --sample 150 --out eval/data/candidates.jsonl

# 2. Interactively label them (resume-friendly)
python eval/scripts/interactive_label.py --candidates eval/data/candidates.jsonl --gold eval/data/gold.jsonl

# 3. Run evaluation (forces fresh classification against current prompts)
python eval/scripts/run_eval.py --gold eval/data/gold.jsonl --force

# View the human-readable report
Get-Content (Get-ChildItem eval/results/eval-*.md | Sort LastWriteTime -Descending | Select -First 1)
```

## Folder Layout

```
eval/
├── README.md
├── EVAL_GUIDE.md           # MUST READ — label definitions + decision rules
├── data/
│   ├── gold.jsonl          # THE golden dataset (commit this)
│   ├── candidates.jsonl    # temp, gitignored
│   ├── video_urls.txt      # sources for future collection
│   └── .eval_cache.sqlite3 # created at runtime (gitignored)
├── scripts/
│   ├── collect_candidates.py
│   ├── interactive_label.py
│   ├── run_eval.py
│   └── ...
├── metrics.py
└── results/                # timestamped reports (.json + .md)
```

## Core Scripts

| Script                    | Purpose                                      | Key Flags                     |
|---------------------------|----------------------------------------------|-------------------------------|
| `collect_candidates.py`   | Sample unique comments from outputs/ (or scrape) | `--sample N`, `--out PATH`   |
| `interactive_label.py`    | Human labeling CLI with resume + validation  | `--candidates`, `--gold`     |
| `run_eval.py`             | Run inference + compute metrics + save report| `--gold`, `--force`, `--limit` |

All scripts set an isolated classification cache (`data/.eval_cache.sqlite3`) so they never touch the main app's cache.

## Gold Dataset Format (JSONL)

See `EVAL_GUIDE.md` for full label semantics.

Example line:

```json
{"id":"a3f9c2","text":"Can you cover corporate politics? I failed for years because of it.","gold_label":"questions","source":"10 Lessons..._comments.csv","labeled_at":"2026-06-30T...","labeler_notes":"Clear ask"}
```

- `id`, `text`, `gold_label` are required.
- `gold_label` must be one of the 7 canonical values.
- Add notes liberally on difficult items.

## Metrics Reported

- Overall accuracy
- Per-class: precision, recall, F1, support
- Macro-F1
- Confusion matrix (ascii table)
- Top confused pairs
- Sample of misclassified items with the raw LLM response

## Improving the Classifier Using Eval

Typical loop:

1. Run eval → look at errors.
2. Edit prompt text inside `backend/classifier.py` (or `_normalize_label`).
3. `python eval/scripts/run_eval.py --gold ... --force`
4. Compare reports (check accuracy delta + specific error cases fixed).
5. Commit the new gold + a snapshot of the report if it shows improvement.

The raw responses in reports are gold for debugging parsing or prompt issues.

## Adding More Data Later

- Edit `eval/data/video_urls.txt`
- Run collect with `--from-urls` (future enhancement) or manually scrape via Gradio/API and drop new CSVs in `backend/outputs/`
- Label the new candidates and append to gold.

## Advanced / Future

- Add `rich` for prettier tables (optional)
- Regression gate in CI (fail if macro-F1 drops below baseline)
- Prompt versioning (extract prompts from classifier into `eval/prompts/`)
- Stratified analysis by video source

## Commands Reference

```powershell
# Quick 20-item smoke test
python eval/scripts/collect_candidates.py --sample 20 --out eval/data/candidates.jsonl
python eval/scripts/interactive_label.py --candidates eval/data/candidates.jsonl --gold eval/data/gold.jsonl
python eval/scripts/run_eval.py --gold eval/data/gold.jsonl --force --limit 20
```

See `EVAL_GUIDE.md` before you start labeling.

Happy evaluating!
