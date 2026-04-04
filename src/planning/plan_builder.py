"""Assemble API-facing plan payloads from planning outputs."""

from __future__ import annotations

from typing import Any

import pandas as pd

from planning.prerequisite_resolver import PrerequisiteParseResult


def build_recommendation_items(
    selected_ids: list[int],
    enriched: pd.DataFrame,
    reasons_by_id: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """Build list of recommendation dicts for JSON response.

    Args:
        selected_ids: Final ordered course ids.
        enriched: Enriched course master dataframe.
        reasons_by_id: Optional map of course_id -> short reason string.

    Returns:
        List of serializable recommendation objects.
    """
    reasons_by_id = reasons_by_id or {}
    if enriched.empty:
        return []
    by_id: dict[int, pd.Series] = {}
    for _, row in enriched.iterrows():
        try:
            cid = int(float(row.get("Course ID")))
        except (TypeError, ValueError):
            continue
        by_id[cid] = row

    out: list[dict[str, Any]] = []
    for cid in selected_ids:
        row = by_id.get(cid)
        if row is None:
            continue
        prereq = row.get("parsed_prerequisite_text")
        hours = row.get("parsed_duration_hours")
        try:
            hours_f = float(hours) if hours is not None and str(hours) != "nan" else None
        except (TypeError, ValueError):
            hours_f = None
        out.append(
            {
                "course_id": cid,
                "course_name": str(row.get("Course Full Name", "") or ""),
                "hours": hours_f if hours_f is not None else 2.0,
                "prerequisite": prereq if isinstance(prereq, str) and prereq.strip() else None,
                "reason": reasons_by_id.get(
                    cid,
                    "Selected based on practice relevance and training hour fit.",
                ),
            }
        )
    return out


def attach_prereq_metadata(
    enriched: pd.DataFrame,
) -> dict[int, PrerequisiteParseResult]:
    """Build prerequisite parse map from enriched columns."""
    result: dict[int, PrerequisiteParseResult] = {}
    for _, row in enriched.iterrows():
        try:
            cid = int(float(row.get("Course ID")))
        except (TypeError, ValueError):
            continue
        raw = row.get("parsed_prerequisite_text")
        mapped = row.get("mapped_prerequisite_course_id")
        try:
            mapped_int = int(float(mapped)) if mapped is not None and str(mapped) != "nan" else None
        except (TypeError, ValueError):
            mapped_int = None
        note = row.get("prerequisite_map_note")
        result[cid] = PrerequisiteParseResult(
            raw_text=str(raw) if raw is not None and str(raw) != "nan" else None,
            mapped_prerequisite_course_id=mapped_int,
            note=str(note) if note else None,
        )
    return result
