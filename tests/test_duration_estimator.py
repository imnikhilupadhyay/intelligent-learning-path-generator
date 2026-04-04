"""Tests for duration parsing."""

from __future__ import annotations

from planning.duration_estimator import estimate_duration_hours, parse_duration_from_text


def test_parse_hours_variants() -> None:
    """Recognize common duration phrasing."""
    assert parse_duration_from_text("This is a 3 hour module.") is not None
    parsed = parse_duration_from_text("This is a 3 hour module.")
    assert parsed is not None and parsed.hours == 3.0


def test_fallback_estimate() -> None:
    """Fallback hours applied when no pattern matches."""
    est = estimate_duration_hours("No duration here", title="Mystery course")
    assert est.source == "fallback"
    assert est.hours >= 1.0
