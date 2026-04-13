"""Hour selection tests."""

from __future__ import annotations

from planning.hour_optimizer import select_courses_for_hours


def test_select_respects_target() -> None:
    """Greedy selection stops near remaining hours."""
    ordered = [1, 2, 3]
    hours = {1: 5.0, 2: 5.0, 3: 10.0}
    res = select_courses_for_hours(ordered, hours, remaining_hours=7.0)
    assert res.selected_course_ids == [1]
    assert res.planned_hours == 5.0


def test_empty_remaining() -> None:
    """No courses when goal already met."""
    res = select_courses_for_hours([1, 2], {1: 1.0, 2: 1.0}, remaining_hours=0.0)
    assert res.selected_course_ids == []
    assert "No remaining" in res.warnings[0]
