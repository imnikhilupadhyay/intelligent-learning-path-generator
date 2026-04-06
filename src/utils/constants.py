"""Repository-wide path and name constants."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
CHROMA_DIR: Path = PROJECT_ROOT / "data" / "chroma" / "learning_catalog_db"
EVALUATION_DIR: Path = PROJECT_ROOT / "data" / "evaluation"
EVALUATION_RUN_IDS_DIR: Path = EVALUATION_DIR / "run_ids"
EVALUATION_SESSION_RUNS_DIR: Path = EVALUATION_DIR / "session_runs"
EVALUATION_SESSION_CSV: Path = EVALUATION_RUN_IDS_DIR / "session.csv"
CONFIG_DIR: Path = PROJECT_ROOT / "config"

RAW_WORKBOOK_BASE: Path = Path(
    os.environ.get("LEARNING_PATH_RAW_DIR", str(DATA_RAW_DIR)),
).expanduser().resolve()

# Default raw Excel names: workflow snake_case first, then common capstone export names.
USER_MASTER_RAW_CANDIDATES: tuple[str, ...] = ("user_master.xlsx", "User Master List.xlsx")
COMPLETION_RAW_CANDIDATES: tuple[str, ...] = ("completion_data.xlsx", "Completion Data.xlsx")
COURSE_MASTER_RAW_CANDIDATES: tuple[str, ...] = ("course_master.xlsx", "Course Master List.xlsx")


def _resolve_raw_workbook(
    candidate_names: tuple[str, ...],
    env_override: str | None,
) -> Path:
    """Resolve path to a raw Excel workbook.

    If ``env_override`` is set in the environment, that path wins. Otherwise the
    first existing file under ``LEARNING_PATH_RAW_DIR`` (or ``data/raw``) matching
    one of ``candidate_names`` is used. If none exist, returns
    ``<raw_base>/<first_candidate>`` for error messages.

    Args:
        candidate_names: File names to try in order (first match wins).
        env_override: Environment variable for a full path override.

    Returns:
        Absolute path chosen for the workbook.
    """
    if env_override and os.environ.get(env_override):
        return Path(os.environ[env_override]).expanduser().resolve()
    for name in candidate_names:
        p = (RAW_WORKBOOK_BASE / name).resolve()
        if p.is_file():
            return p
    return (RAW_WORKBOOK_BASE / candidate_names[0]).resolve()


USER_MASTER_RAW: Path = _resolve_raw_workbook(
    USER_MASTER_RAW_CANDIDATES,
    "LEARNING_PATH_USER_MASTER_XLSX",
)
COMPLETION_RAW: Path = _resolve_raw_workbook(
    COMPLETION_RAW_CANDIDATES,
    "LEARNING_PATH_COMPLETION_XLSX",
)
COURSE_MASTER_RAW: Path = _resolve_raw_workbook(
    COURSE_MASTER_RAW_CANDIDATES,
    "LEARNING_PATH_COURSE_MASTER_XLSX",
)

USER_MASTER_CSV: Path = DATA_PROCESSED_DIR / "user_master.csv"
COMPLETION_CSV: Path = DATA_PROCESSED_DIR / "completion_data.csv"
COURSE_MASTER_CSV: Path = DATA_PROCESSED_DIR / "course_master.csv"
COURSE_MASTER_ENRICHED_CSV: Path = DATA_PROCESSED_DIR / "course_master_enriched.csv"

PRACTICE_MAP_YAML: Path = CONFIG_DIR / "practice_skill_map.yaml"
RETRIEVAL_CONFIG_YAML: Path = CONFIG_DIR / "retrieval_config.yaml"
PARSER_CONFIG_YAML: Path = CONFIG_DIR / "parser_config.yaml"

# Normalized column names used after preprocessing
COL_PORTAL_ID = "Portal ID"
COL_COURSE_ID = "Course ID"
COL_COMPLETION_STATUS = "Completion Status"
COL_TRAINING_GOAL = "Training Goal"
COL_EMP_PRACTISE = "emp_practise"
COL_COURSE_FULL_NAME = "Course Full Name"
COL_SUMMARY = "summary"

COMPLETION_STATUS_COMPLETED = "completed"

_RETRIEVAL_TOP_K_MIN = 1
_RETRIEVAL_TOP_K_MAX = 200
_RETRIEVAL_TOP_K_DEFAULT = 15


def get_retrieval_top_k() -> int:
    """Return hybrid retrieval breadth from ``LEARNING_PATH_TOP_K``.

    Used by the API planner (not exposed in the Streamlit UI). Unset or invalid
    values fall back to 15; result is clamped to [1, 200].

    Returns:
        Integer ``top_k`` for Chroma and keyword candidate retrieval.
    """
    raw = os.environ.get("LEARNING_PATH_TOP_K")
    if raw is None or str(raw).strip() == "":
        return _RETRIEVAL_TOP_K_DEFAULT
    try:
        k = int(str(raw).strip(), 10)
    except ValueError:
        return _RETRIEVAL_TOP_K_DEFAULT
    return max(_RETRIEVAL_TOP_K_MIN, min(_RETRIEVAL_TOP_K_MAX, k))
