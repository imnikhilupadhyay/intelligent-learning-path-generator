"""Business metrics for the deterministic planner (extend with labeled fixtures)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RuleEngineSample:
    """One labeled scenario for offline evaluation."""

    portal_id: int
    must_exclude_completed: Sequence[int]
    should_include_topics: Sequence[str]


def completed_exclusion_accuracy(selected: Sequence[int], completed: Iterable[int]) -> float:
    """Fraction of recommendations that are not in the completed set.

    Args:
        selected: Recommended course ids.
        completed: Completed course ids.

    Returns:
        Score in [0, 1]; 1.0 means no completed leakage.
    """
    c = set(completed)
    if not selected:
        return 1.0
    bad = sum(1 for x in selected if x in c)
    return 1.0 - (bad / len(selected))


def training_goal_coverage(planned_hours: float, target_hours: float) -> float:
    """Ratio of planned hours to annual target.

    Args:
        planned_hours: Hours in the produced plan.
        target_hours: Annual goal.

    Returns:
        Coverage ratio capped at 1.0 for reporting convenience.
    """
    if target_hours <= 0:
        return 0.0
    return min(1.0, planned_hours / target_hours)


def practice_keyword_precision(
    course_texts: Sequence[str],
    keywords: Iterable[str],
) -> float:
    """Share of courses that hit at least one practice keyword (proxy)."""
    kws = [k.lower() for k in keywords if k]
    if not course_texts or not kws:
        return 0.0
    hits = 0
    for text in course_texts:
        low = text.lower()
        if any(k in low for k in kws):
            hits += 1
    return hits / len(course_texts)
