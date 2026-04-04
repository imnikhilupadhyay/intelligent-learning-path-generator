"""Completion filtering tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from services.completion_service import CompletionService


def test_completed_course_ids_filters_status(tmp_path: Path) -> None:
    """Only `completed` status rows count as done."""
    csv_path = tmp_path / "completion.csv"
    df = pd.DataFrame(
        [
            {"Portal ID": 1, "Course ID": 10, "Completion Status": "completed"},
            {"Portal ID": 1, "Course ID": 11, "Completion Status": "in progress"},
        ],
    )
    df.to_csv(csv_path, index=False)
    svc = CompletionService(csv_path=str(csv_path))
    assert svc.completed_course_ids(1) == {10}
