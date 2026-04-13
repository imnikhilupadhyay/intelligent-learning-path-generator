"""Persist plan runs: session CSV + per-run JSON for RAGAS and auditing."""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.constants import (
    EVALUATION_DIR,
    EVALUATION_RUN_IDS_DIR,
    EVALUATION_SESSION_CSV,
    EVALUATION_SESSION_RUNS_DIR,
)


def is_valid_run_id(run_id: str) -> bool:
    """Return True if ``run_id`` is a UUID string (safe for filenames)."""
    if not run_id or not str(run_id).strip():
        return False
    try:
        uuid.UUID(str(run_id).strip())
    except ValueError:
        return False
    return True


def session_json_path(run_id: str) -> Path:
    """Path to ``<run_id>_session.json`` under ``data/evaluation/session_runs``."""
    if not is_valid_run_id(run_id):
        raise ValueError(f"Invalid run_id: {run_id!r}")
    return EVALUATION_SESSION_RUNS_DIR / f"{run_id.strip()}_session.json"


def ensure_evaluation_dirs() -> None:
    """Create evaluation directories if missing."""
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_RUN_IDS_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_SESSION_RUNS_DIR.mkdir(parents=True, exist_ok=True)


def append_session_csv_row(run_id: str, portal_id: int, timestamp_iso: str | None = None) -> None:
    """Append one row to ``session.csv`` (new run_id only)."""
    ensure_evaluation_dirs()
    ts = timestamp_iso or datetime.now(timezone.utc).isoformat()
    file_exists = EVALUATION_SESSION_CSV.is_file()
    with EVALUATION_SESSION_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["run_id", "timestamp", "portal_id"])
        w.writerow([run_id, ts, portal_id])


def write_session_json(run_id: str, payload: dict[str, Any]) -> Path:
    """Write full session payload (API response + evaluation inputs) to JSON."""
    path = session_json_path(run_id)
    ensure_evaluation_dirs()
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def load_session_json(run_id: str) -> dict[str, Any] | None:
    """Load session JSON; return ``None`` if missing or invalid id.

    Reads from ``session_runs/`` first; falls back to legacy ``evaluation/<run_id>_session.json``.
    """
    if not is_valid_run_id(run_id):
        return None
    rid = run_id.strip()
    path = session_json_path(rid)
    if not path.is_file():
        legacy = EVALUATION_DIR / f"{rid}_session.json"
        if legacy.is_file():
            path = legacy
        else:
            return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def resolve_run_id(
    portal_id: int,
    session_run_id: str | None,
) -> tuple[str, bool]:
    """Pick run_id for this request and whether it is brand-new.

    Reuses ``session_run_id`` when the stored session exists and ``portal_id`` matches.

    Args:
        portal_id: Requested employee portal id.
        session_run_id: Optional UUID from client (same browser session, same portal).

    Returns:
        ``(run_id, is_new_run)`` where ``is_new_run`` means append to session CSV.
    """
    if session_run_id and is_valid_run_id(session_run_id):
        data = load_session_json(session_run_id.strip())
        if data is not None:
            try:
                stored_pid = int(data.get("portal_id"))
            except (TypeError, ValueError):
                stored_pid = -1
            if stored_pid == portal_id:
                return session_run_id.strip(), False
    return str(uuid.uuid4()), True


def new_run_id() -> str:
    """Generate a fresh UUID run id."""
    return str(uuid.uuid4())
