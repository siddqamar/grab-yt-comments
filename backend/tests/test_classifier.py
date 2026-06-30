"""Tests for classifier.py - focus on pure logic.

_normalize_label is critical for quality.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from classifier import _normalize_label, LABELS


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("appreciation", "appreciation"),
        ("Appreciation!", "appreciation"),
        ("praise", "appreciation"),
        ("Thank you so much", "appreciation"),
        ("positive feedback", "appreciation"),
        ("humor", "humor"),
        ("humour", "humor"),
        ("joke", "humor"),
        ("FUNNY", "humor"),
        ("questions", "questions"),
        ("Question?", "questions"),
        ("criticism", "criticism"),
        ("critique", "criticism"),
        ("complaint", "criticism"),
        ("negative", "criticism"),
        ("personal experience", "personal experience"),
        ("experience", "personal experience"),
        ("story", "personal experience"),
        ("feedback", "feedback"),
        ("suggestion", "feedback"),
        ("feature request", "feedback"),
        ("spam", "spam"),
        ("scam", "spam"),
        ("bot", "spam"),
        ("unknown label here", "feedback"),  # default
        ("  Mixed_Case-Label  ", "feedback"),  # falls back
    ],
)
def test_normalize_label(raw: str, expected: str):
    assert _normalize_label(raw) == expected


def test_normalize_label_all_valid_labels():
    """Ensure all official labels normalize to themselves."""
    for label in LABELS:
        assert _normalize_label(label) == label
        assert _normalize_label(label.upper()) == label
