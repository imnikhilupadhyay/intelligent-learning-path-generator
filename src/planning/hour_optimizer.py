"""Select ordered courses to best fit remaining training hours."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class HourPlanResult:
    """Courses selected for hour target."""

    selected_course_ids: list[int]
    planned_hours: float
    warnings: list[str]


def select_courses_for_hours(
    ordered_course_ids: Sequence[int],
    hours_by_course_id: dict[int, float],
    remaining_hours: float,
    allow_overshoot_hours: float = 2.0,
) -> HourPlanResult:
    """Greedy selection following ``ordered_course_ids`` order.

    Args:
        ordered_course_ids: Course ids in prerequisite-safe order.
        hours_by_course_id: Estimated hours per course.
        remaining_hours: Hours left to allocate toward the annual goal.
        allow_overshoot_hours: Extra hours allowed beyond target when adding one more course.

    Returns:
        :class:`HourPlanResult` with selected ids and totals.
    """
    warnings: list[str] = []
    selected: list[int] = []
    planned = 0.0
    if remaining_hours <= 0:
        return HourPlanResult(selected_course_ids=[], planned_hours=0.0, warnings=["No remaining target hours."])

    for cid in ordered_course_ids:
        hrs = float(hours_by_course_id.get(cid, 2.0))
        if planned >= remaining_hours:
            break
        if planned + hrs <= remaining_hours + allow_overshoot_hours or planned < remaining_hours * 0.5:
            selected.append(cid)
            planned += hrs
        if planned >= remaining_hours:
            break

    if not selected and ordered_course_ids:
        warnings.append("Could not place courses within hour constraints; returning highest-priority course.")
        cid = ordered_course_ids[0]
        selected = [cid]
        planned = float(hours_by_course_id.get(cid, 2.0))

    return HourPlanResult(
        selected_course_ids=selected,
        planned_hours=round(planned, 2),
        warnings=warnings,
    )


def sum_hours(course_ids: Iterable[int], hours_by_course_id: dict[int, float]) -> float:
    """Sum known hours for course ids."""
    total = 0.0
    for cid in course_ids:
        total += float(hours_by_course_id.get(int(cid), 0.0))
    return round(total, 2)
