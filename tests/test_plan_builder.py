"""Plan assembly tests."""

from __future__ import annotations

import pandas as pd

from planning.plan_builder import build_recommendation_items


def test_build_recommendation_items() -> None:
    """Serialize recommendation dicts from a dataframe."""
    df = pd.DataFrame(
        [
            {
                "Course ID": 5,
                "Course Full Name": "Example",
                "parsed_duration_hours": 2.5,
                "parsed_prerequisite_text": None,
                "summary": "x",
            },
        ],
    )
    items = build_recommendation_items([89, 5], df, {89: "Not in df", 5: "Because skills"})
    assert len(items) == 1
    assert items[0]["course_id"] == 5
