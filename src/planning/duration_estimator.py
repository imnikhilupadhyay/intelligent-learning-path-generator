"""Parse or estimate course duration from summary text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from utils.constants import PARSER_CONFIG_YAML
from utils.file_utils import load_yaml_cached


@dataclass(frozen=True)
class DurationEstimate:
    """Result of duration parsing."""

    hours: float
    confidence: float
    source: str


def _load_parser_patterns() -> Sequence[str]:
    """Load duration regex patterns from parser config."""
    cfg: Mapping[str, Any] = load_yaml_cached(PARSER_CONFIG_YAML)
    patterns = cfg.get("duration_patterns") or []
    if not patterns:
        return [
            r"(?i)(\d+)\s*hours?",
            r"(?i)duration\s*[:\-]?\s*(\d+)",
            r"(?i)(\d+)\s*hr\b",
        ]
    return [str(p) for p in patterns]


def _default_hours_when_missing() -> float:
    cfg: Mapping[str, Any] = load_yaml_cached(PARSER_CONFIG_YAML)
    return float(cfg.get("default_duration_hours_when_missing", 2))


def parse_duration_from_text(summary: str) -> DurationEstimate | None:
    """Extract duration in hours from free text.

    Args:
        summary: Course summary or combined text.

    Returns:
        :class:`DurationEstimate` if a match is found, else ``None``.
    """
    if not summary or not isinstance(summary, str):
        return None
    best: tuple[int, str] | None = None
    for pattern in _load_parser_patterns():
        for m in re.finditer(pattern, summary):
            try:
                hrs = int(m.group(1))
            except (IndexError, ValueError):
                continue
            if best is None or hrs > best[0]:
                best = (hrs, pattern)
    if best is None:
        return None
    return DurationEstimate(hours=float(best[0]), confidence=0.85, source="regex")


def estimate_duration_hours(summary: str | None, title: str | None = None) -> DurationEstimate:
    """Return duration from summary/title with conservative fallback.

    Args:
        summary: Course summary.
        title: Course title (also scanned).

    Returns:
        :class:`DurationEstimate` including fallback when nothing parses.
    """
    combined = " ".join(x for x in [summary or "", title or ""] if x)
    parsed = parse_duration_from_text(combined)
    if parsed is not None:
        return parsed
    fallback = _default_hours_when_missing()
    return DurationEstimate(hours=fallback, confidence=0.2, source="fallback")
