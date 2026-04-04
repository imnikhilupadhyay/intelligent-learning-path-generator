"""Load and query user master records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


from services.practice_mapper import normalize_practice
from utils.constants import (
    COL_EMP_PRACTISE,
    COL_PORTAL_ID,
    COL_TRAINING_GOAL,
    USER_MASTER_CSV,
)
from utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class EmployeeProfile:
    """Subset of user master fields used by planning."""

    portal_id: int
    employee_name: str | None
    grade: float | None
    practice: str | None
    practice_normalized: str | None
    annual_training_goal_hours: float | None
    raw_row: dict[str, Any]


class UserService:
    """Pandas-backed user master access."""

    def __init__(self, csv_path: str | None = None) -> None:
        """Initialize service.

        Args:
            csv_path: Optional override path to processed user_master.csv.
        """
        self._csv_path = csv_path or str(USER_MASTER_CSV)
        self._df: pd.DataFrame | None = None

    def load(self) -> pd.DataFrame:
        """Load dataframe from disk (cached).

        Returns:
            User master dataframe.

        Raises:
            FileNotFoundError: If CSV does not exist.
        """
        if self._df is None:
            path = self._csv_path
            self._df = pd.read_csv(path)
            logger.info("Loaded user master: %s rows from %s", len(self._df), path)
        return self._df

    def all_portal_ids(self) -> set[int]:
        """Return every ``Portal ID`` present in user master.

        Returns:
            Set of portal IDs as integers.

        Raises:
            KeyError: If the expected column is missing.
        """
        df = self.load()
        col = COL_PORTAL_ID
        if col not in df.columns:
            raise KeyError(f"Missing column {col!r} in user master")
        out: set[int] = set()
        for raw in df[col].tolist():
            try:
                out.add(int(float(raw)))
            except (TypeError, ValueError):
                continue
        return out

    def get_by_portal_id(self, portal_id: int) -> EmployeeProfile | None:
        """Fetch employee by portal id.

        Args:
            portal_id: Employee portal identifier.

        Returns:
            :class:`EmployeeProfile` or ``None`` if missing.
        """
        df = self.load()
        col = COL_PORTAL_ID
        if col not in df.columns:
            raise KeyError(f"Missing column {col!r} in user master")
        matches = df[df[col].astype(str) == str(portal_id)]
        if matches.empty:
            return None
        row = matches.iloc[0]
        goal = row.get(COL_TRAINING_GOAL)
        try:
            goal_f = float(goal) if goal is not None and str(goal) != "nan" else None
        except (TypeError, ValueError):
            goal_f = None
        grade = row.get("grade")
        try:
            grade_f = float(grade) if grade is not None and str(grade) != "nan" else None
        except (TypeError, ValueError):
            grade_f = None
        practice = row.get(COL_EMP_PRACTISE)
        practice_s = str(practice).strip() if practice is not None and str(practice) != "nan" else None
        name = row.get("employee_name")
        if name is None or str(name) == "nan":
            # tolerate alternate column naming from source
            for alt in ("Employee Name", "Name", "Full Name"):
                if alt in row.index and str(row.get(alt)) != "nan":
                    name = row.get(alt)
                    break
        return EmployeeProfile(
            portal_id=int(portal_id),
            employee_name=str(name) if name is not None and str(name) != "nan" else None,
            grade=grade_f,
            practice=practice_s,
            practice_normalized=normalize_practice(practice_s),
            annual_training_goal_hours=goal_f,
            raw_row=row.to_dict(),
        )
