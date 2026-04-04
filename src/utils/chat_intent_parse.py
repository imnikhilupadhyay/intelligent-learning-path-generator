"""Parse portal ID and optional target expertise from free-form user text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class LearningPlanIntent:
    """Structured intent extracted from a natural-language message."""

    explicit_portal_id: int | None
    target_expertise: str | None
    integers_in_order: list[int]


_PORTAL_LABEL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?i)\b(?:portal|employee|user)\s*(?:id)?\s*[:#=]?\s*(\d{2,})\b",
    ),
    re.compile(r"(?i)\b(?:id|no\.?)\s*[:=]\s*(\d{2,})\b"),
    re.compile(r"(?i)\b#\s*(\d{2,})\b"),
)

_INTEGER_PATTERN = re.compile(r"\b(\d{2,})\b")

_EXPERTISE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bfocus(?:\s+on)?\s+(.+?)(?:[.,;!?]|\n|$)"),
    re.compile(r"(?i)\bexpertise\s+(?:in|on|:)\s*(.+?)(?:[.,;!?]|\n|$)"),
    re.compile(r"(?i)\btarget\s+(?:expertise\s+)?(?:is|:)?\s*(.+?)(?:[.,;!?]|\n|$)"),
    re.compile(r"(?i)\blearn(?:ing)?\s+(.+?)(?:[.,;!?]|\n|$)"),
    re.compile(r"(?i)\bskills?\s+(?:in|on)\s+(.+?)(?:[.,;!?]|\n|$)"),
    re.compile(r"(?i)\b(?:interested\s+in|want\s+to\s+learn)\s+(.+?)(?:[.,;!?]|\n|$)"),
)


def _clean_expertise_fragment(raw: str) -> str | None:
    """Normalize expertise text; reject pure numbers or empty."""
    s = raw.strip().strip("\"'").strip()
    s = re.sub(r"\s+", " ", s)
    if not s or re.fullmatch(r"\d+", s):
        return None
    if len(s) > 80:
        s = s[:80].rsplit(" ", 1)[0]
    return s or None


def _extract_expertise(text: str) -> str | None:
    """First matching expertise phrase from patterns."""
    for pat in _EXPERTISE_PATTERNS:
        m = pat.search(text)
        if m:
            hit = _clean_expertise_fragment(m.group(1))
            if hit:
                return hit
    return None


def _extract_explicit_portal(text: str) -> int | None:
    """Portal ID from labeled phrases like ``portal id 12345``."""
    for pat in _PORTAL_LABEL_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                return int(m.group(1))
            except (TypeError, ValueError):
                continue
    return None


def _integers_in_order(text: str) -> list[int]:
    """All 2+ digit integers in left-to-right order, deduped while preserving order."""
    seen: set[int] = set()
    ordered: list[int] = []
    for m in _INTEGER_PATTERN.finditer(text):
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def parse_learning_plan_intent(message: str) -> LearningPlanIntent:
    """Pull portal hints and expertise from natural language.

    Args:
        message: User chat line (e.g. ``Plan for portal 24463, focus on Java``).

    Returns:
        Parsed :class:`LearningPlanIntent` (portal may still need DB resolution).
    """
    text = (message or "").strip()
    if not text:
        return LearningPlanIntent(None, None, [])
    explicit = _extract_explicit_portal(text)
    expertise = _extract_expertise(text)
    ints = _integers_in_order(text)
    return LearningPlanIntent(
        explicit_portal_id=explicit,
        target_expertise=expertise,
        integers_in_order=ints,
    )


def resolve_portal_id(
    intent: LearningPlanIntent,
    valid_portal_ids: Iterable[int],
) -> int | None:
    """Choose a portal ID using explicit labels first, then integers present in text.

    Args:
        intent: Parsed intent from :func:`parse_learning_plan_intent`.
        valid_portal_ids: Known portal IDs from user master (e.g. CSV).

    Returns:
        Matched portal ID, or ``None`` if no ID appears in ``valid_portal_ids``.
    """
    valid = set(valid_portal_ids)
    if not valid:
        return None
    candidates: list[int] = []
    if intent.explicit_portal_id is not None:
        candidates.append(intent.explicit_portal_id)
    for n in intent.integers_in_order:
        if n not in candidates:
            candidates.append(n)
    for c in candidates:
        if c in valid:
            return c
    return None


def explain_portal_resolution_failure(intent: LearningPlanIntent) -> str:
    """Short user-facing hint when no portal ID matches the directory."""
    if intent.explicit_portal_id is not None:
        return (
            f"I found portal **{intent.explicit_portal_id}** in your message, but that ID "
            "is not in the user directory. Try a portal ID that exists in the user master data."
        )
    if intent.integers_in_order:
        shown = ", ".join(str(x) for x in intent.integers_in_order[:5])
        return (
            "I spotted these numbers: "
            f"{shown}. None match an employee **Portal ID** in the loaded user data. "
            'Please include a valid portal ID (e.g. "portal id 12345").'
        )
    return (
        'I need an employee **portal ID** in your message (e.g. "24463" or "portal id 24463"). '
        'Optionally add a focus like "focus on Java".'
    )
