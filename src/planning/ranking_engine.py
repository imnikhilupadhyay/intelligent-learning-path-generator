"""Score and rank course candidates for an employee context."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import pandas as pd

from utils.text_utils import count_keyword_hits, lowercase_copy


@dataclass(frozen=True)
class RankWeights:
    """Weights for the hybrid ranking formula."""

    practice: float = 0.35
    semantic: float = 0.25
    expertise: float = 0.15
    grade_fit: float = 0.10
    prerequisite_readiness: float = 0.10
    support_bonus: float = 0.05


def _grade_fit(course_grade_hint: str | None, employee_grade: float | None) -> float:
    if employee_grade is None or course_grade_hint is None:
        return 0.5
    m = re.search(r"(\d+)", str(course_grade_hint))
    if not m:
        return 0.5
    try:
        g = int(m.group(1))
    except ValueError:
        return 0.5
    diff = abs(float(g) - float(employee_grade))
    return max(0.0, 1.0 - diff / 10.0)


def compute_scores(
    candidates: pd.DataFrame,
    practice_keywords: Sequence[str],
    target_expertise: str | None,
    semantic_scores: Mapping[Any, float] | None,
    employee_grade: float | None,
    completed_ids: set[int],
    weights: RankWeights | None = None,
) -> pd.DataFrame:
    """Add score columns and ``final_score`` to candidate rows.

    Args:
        candidates: Subset of enriched course master rows.
        practice_keywords: Keywords from practice mapping.
        target_expertise: Optional employee target expertise string.
        semantic_scores: Optional map course_id -> [0,1] similarity.
        employee_grade: Numeric grade if available.
        completed_ids: Completed course ids (for readiness proxy).
        weights: Optional custom weights.

    Returns:
        Copy of candidates with scoring columns.
    """
    w = weights or RankWeights()
    df = candidates.copy()
    if df.empty:
        df["final_score"] = []
        return df

    expertise_kw: list[str] = []
    if target_expertise:
        expertise_kw = [target_expertise]

    def row_scores(row: pd.Series) -> dict[str, float]:
        cid = row.get("Course ID")
        summary = str(row.get("summary_lower", row.get("summary", "")) or "")
        title = str(row.get("Course Full Name", "") or "")
        haystack = f"{lowercase_copy(title)} {summary}"

        practice_match = min(
            1.0,
            count_keyword_hits(haystack, practice_keywords) / max(1, len(practice_keywords)) * 2.5,
        )
        expertise_match = (
            1.0
            if target_expertise and lowercase_copy(target_expertise) in haystack
            else min(1.0, count_keyword_hits(haystack, expertise_kw) / max(1, len(expertise_kw) or 1))
        )

        sem = 0.5
        if semantic_scores is not None:
            try:
                key = int(float(cid))
            except (TypeError, ValueError):
                key = cid  # type: ignore[assignment]
            sem = float(semantic_scores.get(key, 0.5))

        gfit = _grade_fit(row.get("parsed_grade_hint"), employee_grade)
        prereq_text = row.get("parsed_prerequisite_text")
        readiness = 1.0
        if isinstance(prereq_text, str) and prereq_text.strip():
            readiness = 0.7
        # crude boost if title hits strong practice keyword
        support = 0.2 if practice_match > 0.6 else 0.0

        final = (
            w.practice * practice_match
            + w.semantic * sem
            + w.expertise * expertise_match
            + w.grade_fit * gfit
            + w.prerequisite_readiness * readiness
            + w.support_bonus * min(1.0, support / 0.2)
        )
        return {
            "practice_match_score": practice_match,
            "semantic_similarity_score": sem,
            "expertise_match_score": expertise_match,
            "grade_fit_score": gfit,
            "prerequisite_readiness_score": readiness,
            "support_bonus_score": support,
            "final_score": final,
        }

    scores = df.apply(row_scores, axis=1, result_type="expand")
    out = pd.concat([df.reset_index(drop=True), scores.reset_index(drop=True)], axis=1)
    return out.sort_values("final_score", ascending=False).reset_index(drop=True)


def top_n(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Return top n rows by ``final_score``."""
    if df.empty or n <= 0:
        return df.iloc[0:0]
    return df.nlargest(n, "final_score").reset_index(drop=True)
