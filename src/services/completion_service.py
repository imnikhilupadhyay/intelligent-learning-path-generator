"""Load completion data and completed course sets per employee."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from utils.constants import (
    COL_COMPLETION_STATUS,
    COL_COURSE_ID,
    COL_PORTAL_ID,
    COMPLETION_CSV,
    COMPLETION_STATUS_COMPLETED,
)
from utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class CompletionRecord:
    """Single completion row summary."""

    portal_id: int
    course_id: int
    status: str


class CompletionService:
    """Pandas-backed completion table access."""

    def __init__(self, csv_path: str | None = None) -> None:
        """Initialize service.

        Args:
            csv_path: Optional path to processed completion_data.csv.
        """
        self._csv_path = csv_path or str(COMPLETION_CSV)
        self._df: pd.DataFrame | None = None

    def load(self) -> pd.DataFrame:
        """Load completion dataframe (cached)."""
        if self._df is None:
            self._df = pd.read_csv(self._csv_path)
            logger.info("Loaded completion data: %s rows", len(self._df))
        return self._df

    def completed_course_ids(self, portal_id: int) -> set[int]:
        """Return course ids marked completed for an employee.

        A row counts as completed only when status equals ``completed`` (case-insensitive).

        Args:
            portal_id: Employee portal id.

        Returns:
            Set of completed course ids (ints).
        """
        df = self.load()
        pid_col, cid_col, st_col = COL_PORTAL_ID, COL_COURSE_ID, COL_COMPLETION_STATUS
        for c in (pid_col, cid_col, st_col):
            if c not in df.columns:
                raise KeyError(f"Missing column {c!r} in completion data")
        sub = df[df[pid_col].astype(str) == str(portal_id)]
        done = sub[sub[st_col].astype(str).str.lower().str.strip() == COMPLETION_STATUS_COMPLETED]
        ids: set[int] = set()
        for raw in done[cid_col].tolist():
            try:
                ids.add(int(float(raw)))
            except (TypeError, ValueError):
                continue
        return ids
