"""Enrich course master with parsed metadata columns."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from planning.duration_estimator import estimate_duration_hours
from planning.prerequisite_resolver import extract_prerequisite_text, map_prerequisite_to_course_id
from utils.constants import COL_COURSE_FULL_NAME, COL_COURSE_ID, COL_SUMMARY, COURSE_MASTER_CSV
from utils.constants import COURSE_MASTER_ENRICHED_CSV, DATA_PROCESSED_DIR
from utils.file_utils import ensure_dir
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def _grade_hint(summary: str | None) -> str | None:
    if not summary:
        return None
    m = re.search(r"(?i)grade\s*(\d+)", str(summary))
    if m:
        return m.group(1) + "+"
    m2 = re.search(r"(?i)(?:grade|level)\s*[:\-]?\s*(\d+)", str(summary))
    if m2:
        return m2.group(1) + "+"
    return None


def _audience_snippet(summary: str | None) -> str | None:
    if not summary:
        return None
    m = re.search(r"(?i)(?:intended audience|audience)\s*[:\-]?\s*(.+?)(?:\.|$)", str(summary))
    return m.group(1).strip() if m else None


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return enriched dataframe with parsed columns."""
    out = df.copy()
    durations: list[float] = []
    confidences: list[float] = []
    prereq_texts: list[str | None] = []
    grade_hints: list[str | None] = []
    audiences: list[str | None] = []
    mapped_ids: list[Any] = []
    notes: list[str | None] = []

    for _, row in out.iterrows():
        summary = row.get(COL_SUMMARY)
        title = row.get(COL_COURSE_FULL_NAME)
        est = estimate_duration_hours(
            str(summary) if summary is not None and str(summary) != "nan" else None,
            str(title) if title is not None and str(title) != "nan" else None,
        )
        durations.append(est.hours)
        confidences.append(est.confidence)
        pt = extract_prerequisite_text(str(summary) if summary is not None else None)
        prereq_texts.append(pt)
        grade_hints.append(_grade_hint(str(summary) if summary is not None else None))
        audiences.append(_audience_snippet(str(summary) if summary is not None else None))
        mid, note = map_prerequisite_to_course_id(pt, out, name_col=COL_COURSE_FULL_NAME, id_col=COL_COURSE_ID)
        mapped_ids.append(mid)
        notes.append(note)

    out["parsed_duration_hours"] = durations
    out["duration_parse_confidence"] = confidences
    out["parsed_prerequisite_text"] = prereq_texts
    out["mapped_prerequisite_course_id"] = mapped_ids
    out["prerequisite_map_note"] = notes
    out["parsed_grade_hint"] = grade_hints
    out["parsed_audience_text"] = audiences
    return out


def run_enrichment() -> None:
    """Read processed course_master.csv and write course_master_enriched.csv."""
    ensure_dir(DATA_PROCESSED_DIR)
    base = pd.read_csv(COURSE_MASTER_CSV)
    enriched = enrich_dataframe(base)
    enriched.to_csv(COURSE_MASTER_ENRICHED_CSV, index=False)
    logger.info("Wrote enriched course master: %s", COURSE_MASTER_ENRICHED_CSV)
