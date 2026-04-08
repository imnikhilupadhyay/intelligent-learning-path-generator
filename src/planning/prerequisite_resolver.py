"""Parse prerequisite mentions and map them to catalog course IDs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

import pandas as pd

from utils.text_utils import fold_unicode, lowercase_copy, normalize_whitespace, strip_html_tags


@dataclass(frozen=True)
class PrerequisiteParseResult:
    """Parsed prerequisite information for a single course row."""

    raw_text: str | None
    mapped_prerequisite_course_id: int | None
    note: str | None


_PREREQ_PATTERNS: Sequence[str] = (
    r"(?i)prerequisite[s]?\s*[:\-]?\s*(.+?)(?:\.(?:\s|$)|$)",
    r"(?i)pre-?requisite[s]?\s*[:\-]?\s*(.+?)(?:\.(?:\s|$)|$)",
    r"(?i)required\s+(?:course|training)\s*[:\-]?\s*(.+?)(?:\.(?:\s|$)|$)",
)


def extract_prerequisite_text(summary: str | None) -> str | None:
    """Extract a prerequisite phrase from summary text.

    Args:
        summary: Free-text course summary.

    Returns:
        Trimmed prerequisite fragment or ``None``.
    """
    if not summary or not isinstance(summary, str):
        return None
    plain = strip_html_tags(summary)
    for pat in _PREREQ_PATTERNS:
        m = re.search(pat, plain, flags=re.DOTALL)
        if m:
            text = normalize_whitespace(m.group(1))
            return text or None
    return None


def _similarity_token_overlap(a: str, b: str) -> float:
    """Cheap token overlap score in [0, 1]."""
    ta = {t for t in re.split(r"\W+", fold_unicode(a).lower()) if len(t) > 2}
    tb = {t for t in re.split(r"\W+", fold_unicode(b).lower()) if len(t) > 2}
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def map_prerequisite_to_course_id(
    prerequisite_text: str | None,
    course_catalog: pd.DataFrame,
    name_col: str = "Course Full Name",
    id_col: str = "Course ID",
    min_score: float = 0.34,
) -> tuple[int | None, str | None]:
    """Map prerequisite free text to the best matching course in the catalog.

    Args:
        prerequisite_text: Parsed prerequisite description.
        course_catalog: DataFrame with course ids and names.
        name_col: Column for course display name.
        id_col: Column for numeric/string course id.
        min_score: Minimum overlap score to accept a match.

    Returns:
        Tuple of (course_id or None, advisory note or None).
    """
    if prerequisite_text is None or course_catalog is None or course_catalog.empty:
        return None, None
    best_id: int | None = None
    best_score = 0.0
    best_name: str | None = None
    for _, row in course_catalog.iterrows():
        name = str(row.get(name_col, "") or "")
        if not name:
            continue
        score = max(
            _similarity_token_overlap(prerequisite_text, name),
            1.0 if lowercase_copy(prerequisite_text) in lowercase_copy(name) else 0.0,
            1.0 if lowercase_copy(name) in lowercase_copy(prerequisite_text) else 0.0,
        )
        if score > best_score:
            best_score = score
            raw_id = row.get(id_col)
            try:
                best_id = int(float(raw_id)) if raw_id is not None and str(raw_id) != "nan" else None
            except (TypeError, ValueError):
                best_id = None
            best_name = name
    if best_id is None or best_score < min_score:
        return None, "Prerequisite text could not be mapped to a catalog course."
    return best_id, f"Mapped to catalog course '{best_name}' (score={best_score:.2f})."


def build_ordered_ids_with_prereqs(
    recommended_ids: Iterable[int],
    course_rows_by_id: dict[int, PrerequisiteParseResult],
    completed_ids: set[int],
) -> list[int]:
    """Insert uncompleted prerequisites before dependents when mapping exists.

    Args:
        recommended_ids: Preferred order of course IDs (highest rank first).
        course_rows_by_id: Parsed prerequisite info keyed by course id.
        completed_ids: Already completed course IDs.

    Returns:
        Ordered list with prerequisites inserted ahead of dependents.
    """
    rec_list = list(dict.fromkeys(recommended_ids))
    result: list[int] = []
    seen: set[int] = set()
    visiting: set[int] = set()

    def add_chain(cid: int) -> None:
        """Depth-first prerequisite expansion with cycle and self-loop guards."""
        if cid in seen:
            return
        if cid in visiting:
            # Prerequisite graph has a cycle (e.g. A→B→A); stop this branch.
            return
        visiting.add(cid)
        info = course_rows_by_id.get(cid)
        prereq_id = info.mapped_prerequisite_course_id if info else None
        if (
            prereq_id is not None
            and prereq_id != cid
            and prereq_id not in completed_ids
            and prereq_id not in seen
        ):
            add_chain(prereq_id)
        visiting.discard(cid)
        if cid not in seen:
            result.append(cid)
            seen.add(cid)

    for cid in rec_list:
        add_chain(cid)
    return result
