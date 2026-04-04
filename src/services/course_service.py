"""Course catalog access (processed and enriched)."""

from __future__ import annotations

import os

import pandas as pd

from utils.constants import COURSE_MASTER_CSV, COURSE_MASTER_ENRICHED_CSV
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class CourseService:
    """Load course master CSVs."""

    def __init__(
        self,
        processed_path: str | None = None,
        enriched_path: str | None = None,
    ) -> None:
        """Initialize paths to course CSVs."""
        self._processed_path = processed_path or str(COURSE_MASTER_CSV)
        self._enriched_path = enriched_path or str(COURSE_MASTER_ENRICHED_CSV)
        self._df_enriched: pd.DataFrame | None = None
        self._df_base: pd.DataFrame | None = None

    def load_enriched(self, prefer_enriched: bool = True) -> pd.DataFrame:
        """Load enriched catalog if present, else base processed CSV.

        Args:
            prefer_enriched: When True, use enriched file if it exists.

        Returns:
            Course dataframe.
        """
        if prefer_enriched and os.path.isfile(self._enriched_path):
            if self._df_enriched is None:
                self._df_enriched = pd.read_csv(self._enriched_path)
                logger.info("Loaded enriched course master: %s", len(self._df_enriched))
            return self._df_enriched.copy()
        if self._df_base is None:
            self._df_base = pd.read_csv(self._processed_path)
            logger.info("Loaded course master: %s", len(self._df_base))
        return self._df_base.copy()

    def as_dataframe(self) -> pd.DataFrame:
        """Alias for :meth:`load_enriched`."""
        return self.load_enriched()
