"""Load Excel sources into pandas DataFrames."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.constants import (
    COMPLETION_RAW,
    COMPLETION_RAW_CANDIDATES,
    COURSE_MASTER_RAW,
    COURSE_MASTER_RAW_CANDIDATES,
    RAW_WORKBOOK_BASE,
    USER_MASTER_RAW,
    USER_MASTER_RAW_CANDIDATES,
)
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def assert_raw_workbooks_exist() -> None:
    """Verify required Excel inputs exist before preprocessing.

    Raises:
        FileNotFoundError: If any required workbook is missing, with paths and
            ``.env`` hints (``LEARNING_PATH_RAW_DIR``, per-file overrides).
    """
    specs: list[tuple[str, tuple[str, ...], Path]] = [
        ("User master table", USER_MASTER_RAW_CANDIDATES, USER_MASTER_RAW),
        ("Completion table", COMPLETION_RAW_CANDIDATES, COMPLETION_RAW),
        ("Course catalog", COURSE_MASTER_RAW_CANDIDATES, COURSE_MASTER_RAW),
    ]
    missing = [(label, names, p) for label, names, p in specs if not p.is_file()]
    if not missing:
        return
    lines = [
        "Missing Excel input(s). Ingestion needs these workbooks:",
        f"  (under: {RAW_WORKBOOK_BASE})",
        "",
    ]
    for label, names, p in missing:
        tried = ", ".join(names)
        lines.append(f"  - {label}")
        lines.append(f"    Look for one of: {tried}")
        lines.append(f"    Fallback path checked: {p}")
    lines.extend(
        [
            "",
            "Fix: place the three .xlsx files at the paths above, or set in .env:",
            "  LEARNING_PATH_RAW_DIR=C:\\path\\to\\folder_with_workbooks",
            "Optional per-file overrides (full paths):",
            "  LEARNING_PATH_USER_MASTER_XLSX=...",
            "  LEARNING_PATH_COMPLETION_XLSX=...",
            "  LEARNING_PATH_COURSE_MASTER_XLSX=...",
            "",
            "Run from repo root so python can load `.env` (see run_ingestion.py).",
        ],
    )
    raise FileNotFoundError("\n".join(lines))


def read_user_master(path: str | Path | None = None) -> pd.DataFrame:
    """Read user master workbook.

    Args:
        path: Path to ``user_master.xlsx``; default from constants.

    Returns:
        Raw dataframe.
    """
    p = Path(path or USER_MASTER_RAW)
    df = pd.read_excel(p)
    logger.info("Read user master: %s rows from %s", len(df), p)
    return df


def read_completion_data(path: str | Path | None = None) -> pd.DataFrame:
    """Read completion workbook."""
    p = Path(path or COMPLETION_RAW)
    df = pd.read_excel(p)
    logger.info("Read completion data: %s rows from %s", len(df), p)
    return df


def read_course_master(path: str | Path | None = None) -> pd.DataFrame:
    """Read course master workbook."""
    p = Path(path or COURSE_MASTER_RAW)
    df = pd.read_excel(p)
    logger.info("Read course master: %s rows from %s", len(df), p)
    return df
