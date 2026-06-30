"""Pure-Python metrics for multi-class comment classification evaluation.

No external dependencies (no sklearn/pandas). Designed for small gold sets.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def _safe_div(num: float, den: float) -> float:
    return num / den if den > 0 else 0.0


def compute_accuracy(golds: list[str], preds: list[str]) -> float:
    """Overall accuracy = correct / total."""
    if not golds:
        return 0.0
    correct = sum(1 for g, p in zip(golds, preds) if g == p)
    return correct / len(golds)


def compute_confusion_matrix(
    golds: list[str], preds: list[str], labels: list[str]
) -> dict[str, dict[str, int]]:
    """Return confusion matrix as dict[label_gold][label_pred] = count."""
    mat: dict[str, dict[str, int]] = {lab: {l: 0 for l in labels} for lab in labels}
    for g, p in zip(golds, preds):
        if g in mat and p in mat[g]:
            mat[g][p] += 1
    return mat


def format_confusion_table(
    golds: list[str], preds: list[str], labels: list[str]
) -> str:
    """Return a readable ASCII confusion matrix table."""
    mat = compute_confusion_matrix(golds, preds, labels)
    # Header
    header = ["gold \\ pred"] + labels
    col_widths = [max(len(h), 12) for h in header]

    def fmt_row(row: list[str]) -> str:
        return " | ".join(cell.ljust(w) for cell, w in zip(row, col_widths))

    lines = [fmt_row(header), "-" * (sum(col_widths) + 3 * (len(header) - 1))]

    for g in labels:
        row = [g] + [str(mat[g][p]) for p in labels]
        lines.append(fmt_row(row))

    # Totals row
    totals_pred = [str(sum(mat[g][p] for g in labels)) for p in labels]
    lines.append(fmt_row(["TOTAL pred"] + totals_pred))

    return "\n".join(lines)


def compute_per_class_metrics(
    golds: list[str], preds: list[str], labels: list[str]
) -> dict[str, dict[str, Any]]:
    """
    Per-class precision, recall, f1, support.
    Returns dict[label] = {"precision":, "recall":, "f1":, "support":}
    """
    gold_counts = Counter(golds)
    pred_counts = Counter(preds)
    tp_counts: dict[str, int] = defaultdict(int)

    for g, p in zip(golds, preds):
        if g == p:
            tp_counts[g] += 1

    results: dict[str, dict[str, Any]] = {}
    for lab in labels:
        support = gold_counts.get(lab, 0)
        tp = tp_counts.get(lab, 0)
        fp = pred_counts.get(lab, 0) - tp
        fn = support - tp

        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, support)
        f1 = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) > 0 else 0.0

        results[lab] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }
    return results


def compute_macro_f1(per_class: dict[str, dict[str, Any]]) -> float:
    f1s = [m["f1"] for m in per_class.values()]
    return round(sum(f1s) / len(f1s), 4) if f1s else 0.0


def compute_most_confused_pairs(
    golds: list[str], preds: list[str], labels: list[str], top_k: int = 5
) -> list[tuple[str, str, int]]:
    """Return list of (gold, pred, count) for off-diagonal errors, highest first."""
    errors: Counter[tuple[str, str]] = Counter()
    for g, p in zip(golds, preds):
        if g != p:
            errors[(g, p)] += 1
    return errors.most_common(top_k)


def summarize_label_distribution(
    golds: list[str], preds: list[str], labels: list[str]
) -> dict[str, dict[str, int]]:
    """Return gold vs predicted counts per label."""
    g = Counter(golds)
    p = Counter(preds)
    return {lab: {"gold": g.get(lab, 0), "pred": p.get(lab, 0)} for lab in labels}


def collect_error_examples(
    records: list[dict[str, Any]], max_examples: int = 15
) -> list[dict[str, Any]]:
    """
    Given list of full records (must contain at minimum: text, gold_label, pred_label, raw),
    return up to max_examples of the misclassified ones.
    """
    errors = [r for r in records if r.get("gold_label") != r.get("pred_label")]
    # Sort by some signal (longer texts or just first N)
    errors.sort(key=lambda r: -len(str(r.get("text", ""))))
    return errors[:max_examples]


def build_full_report(
    golds: list[str],
    preds: list[str],
    labels: list[str],
    records: list[dict[str, Any]] | None = None,
    model_name: str = "unknown",
) -> dict[str, Any]:
    """Aggregate everything into a serializable report dict."""
    per_class = compute_per_class_metrics(golds, preds, labels)
    acc = compute_accuracy(golds, preds)
    macro = compute_macro_f1(per_class)
    confused = compute_most_confused_pairs(golds, preds, labels)
    dist = summarize_label_distribution(golds, preds, labels)
    cm_table = format_confusion_table(golds, preds, labels)

    error_examples: list[dict[str, Any]] = []
    if records:
        error_examples = collect_error_examples(records)

    return {
        "model_name": model_name,
        "total": len(golds),
        "accuracy": round(acc, 4),
        "macro_f1": macro,
        "per_class": per_class,
        "most_confused": confused,
        "distribution": dist,
        "confusion_table": cm_table,
        "error_examples": error_examples,
    }


def format_report_markdown(report: dict[str, Any]) -> str:
    """Human friendly markdown summary."""
    lines: list[str] = []
    lines.append("# Classifier Evaluation Report\n")
    lines.append(f"**Model**: {report.get('model_name', 'unknown')}")
    lines.append(f"**Total examples**: {report.get('total', 0)}")
    lines.append(f"**Accuracy**: {report.get('accuracy', 0):.4f}")
    lines.append(f"**Macro F1**: {report.get('macro_f1', 0):.4f}\n")

    lines.append("## Per-Class Metrics\n")
    lines.append("| Label | Precision | Recall | F1 | Support |")
    lines.append("|-------|-----------|--------|----|---------|")
    for lab, m in report.get("per_class", {}).items():
        lines.append(
            f"| {lab} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['support']} |"
        )
    lines.append("")

    lines.append("## Most Confused Pairs (gold → pred)\n")
    for (g, p, cnt) in report.get("most_confused", []):
        lines.append(f"- `{g}` → `{p}` : {cnt}")
    if not report.get("most_confused"):
        lines.append("(none)")
    lines.append("")

    lines.append("## Confusion Matrix\n")
    lines.append("```\n" + report.get("confusion_table", "") + "\n```\n")

    lines.append("## Error Examples (sample)\n")
    for ex in report.get("error_examples", [])[:8]:
        text = str(ex.get("text", ""))[:160].replace("\n", " ")
        lines.append(f"- **gold**: {ex.get('gold_label')} | **pred**: {ex.get('pred_label')}")
        lines.append(f"  `{text}...`")
        if ex.get("raw"):
            raw = str(ex.get("raw", ""))[:120].replace("\n", " ")
            lines.append(f"  raw: `{raw}`")
        lines.append("")
    if not report.get("error_examples"):
        lines.append("(no errors or none captured)")

    return "\n".join(lines)
