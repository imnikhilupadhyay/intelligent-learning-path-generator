"""Clean column names and normalize key fields; persist processed CSVs."""

from __future__ import annotations

import pandas as pd

from services.practice_mapper import normalize_practice
from utils.constants import (
    COL_EMP_PRACTISE,
    COL_SUMMARY,
    COMPLETION_CSV,
    COURSE_MASTER_CSV,
    DATA_PROCESSED_DIR,
    USER_MASTER_CSV,
)
from utils.file_utils import ensure_dir
from utils.logging_utils import get_logger
from utils.text_utils import lowercase_copy

from ingestion.load_excel import (
    assert_raw_workbooks_exist,
    read_completion_data,
    read_course_master,
    read_user_master,
)

logger = get_logger(__name__)


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace from column headers."""
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def preprocess_user_master(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize practice and string fields."""
    d = _clean_columns(df)
    if COL_EMP_PRACTISE in d.columns:
        d[COL_EMP_PRACTISE] = d[COL_EMP_PRACTISE].apply(
            lambda x: normalize_practice(str(x).strip()) if pd.notna(x) else None,
        )
    for col in d.columns:
        if d[col].dtype == object:
            d[col] = d[col].apply(lambda x: str(x).strip() if isinstance(x, str) else x)
    return d


def preprocess_completion(df: pd.DataFrame) -> pd.DataFrame:
    """Trim completion dataframe."""
    d = _clean_columns(df)
    for col in d.columns:
        if d[col].dtype == object:
            d[col] = d[col].apply(lambda x: str(x).strip() if isinstance(x, str) else x)
    return d


def preprocess_course_master(df: pd.DataFrame) -> pd.DataFrame:
    """Add lowercase summary copy."""
    d = _clean_columns(df)
    if COL_SUMMARY in d.columns:
        d["summary_lower"] = d[COL_SUMMARY].apply(lambda x: lowercase_copy(str(x)) if pd.notna(x) else "")
    return d


def run_default_preprocess() -> None:
    """Load raw Excel files and write processed CSVs under ``data/processed``."""
    assert_raw_workbooks_exist()
    ensure_dir(DATA_PROCESSED_DIR)
    u = preprocess_user_master(read_user_master())
    c = preprocess_completion(read_completion_data())
    m = preprocess_course_master(read_course_master())
    u.to_csv(USER_MASTER_CSV, index=False)
    c.to_csv(COMPLETION_CSV, index=False)
    m.to_csv(COURSE_MASTER_CSV, index=False)
    logger.info("Wrote processed CSVs to %s", DATA_PROCESSED_DIR)
