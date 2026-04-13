"""User service tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from services.user_service import UserService


def test_get_by_portal_id(tmp_path: Path) -> None:
    """Load employee profile from CSV."""
    p = tmp_path / "user.csv"
    df = pd.DataFrame(
        [
            {
                "Portal ID": 42,
                "employee_name": "Test User",
                "grade": 5,
                "Training Goal": 12.0,
                "emp_practise": "Global Support",
            },
        ],
    )
    df.to_csv(p, index=False)
    svc = UserService(csv_path=str(p))
    profile = svc.get_by_portal_id(42)
    assert profile is not None
    assert profile.annual_training_goal_hours == 12.0
    assert profile.practice == "Global Support"
