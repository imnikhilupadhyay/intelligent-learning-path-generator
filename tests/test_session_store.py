"""Tests for evaluation session persistence helpers."""

from __future__ import annotations

import json
import uuid

import pytest

import evaluation.session_store as session_store
from evaluation.session_store import (
    append_session_csv_row,
    load_session_json,
    resolve_run_id,
    write_session_json,
)


def _patch_eval_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path, name: str = "eval") -> None:
    ev = tmp_path / name
    run_ids = ev / "run_ids"
    session_runs = ev / "session_runs"
    run_ids.mkdir(parents=True)
    monkeypatch.setattr(session_store, "EVALUATION_DIR", ev)
    monkeypatch.setattr(session_store, "EVALUATION_RUN_IDS_DIR", run_ids)
    monkeypatch.setattr(session_store, "EVALUATION_SESSION_CSV", run_ids / "session.csv")
    monkeypatch.setattr(session_store, "EVALUATION_SESSION_RUNS_DIR", session_runs)


def test_resolve_run_id_mints_new_when_no_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Without a stored JSON, always return a new UUID."""
    _patch_eval_dirs(monkeypatch, tmp_path)

    rid, is_new = resolve_run_id(42, None)
    assert is_new is True
    assert uuid.UUID(rid)


def test_resolve_run_id_reuses_when_portal_matches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Reuse client session id when file exists and portal_id matches."""
    _patch_eval_dirs(monkeypatch, tmp_path)

    rid = str(uuid.uuid4())
    write_session_json(rid, {"portal_id": 7, "run_id": rid, "employee_intro": "x"})

    out, is_new = resolve_run_id(7, rid)
    assert is_new is False
    assert out == rid


def test_resolve_run_id_new_when_portal_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Stale session id for a different portal yields a fresh run_id."""
    _patch_eval_dirs(monkeypatch, tmp_path)

    rid = str(uuid.uuid4())
    write_session_json(rid, {"portal_id": 7, "run_id": rid})

    out, is_new = resolve_run_id(99, rid)
    assert is_new is True
    assert out != rid


def test_append_session_csv_header_and_row(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _patch_eval_dirs(monkeypatch, tmp_path)
    csv_path = session_store.EVALUATION_SESSION_CSV

    append_session_csv_row("abc", 1, "2020-01-01T00:00:00+00:00")
    text = csv_path.read_text(encoding="utf-8")
    assert "run_id" in text
    assert "abc" in text
    assert "1" in text


def test_load_session_json_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _patch_eval_dirs(monkeypatch, tmp_path)

    rid = str(uuid.uuid4())
    payload = {"portal_id": 3, "run_id": rid, "k": "v"}
    write_session_json(rid, payload)
    loaded = load_session_json(rid)
    assert loaded == payload
    path = session_store.session_json_path(rid)
    assert path.parent == session_store.EVALUATION_SESSION_RUNS_DIR
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_load_session_json_legacy_location(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """Still load JSON from pre-session_runs path under evaluation root."""
    _patch_eval_dirs(monkeypatch, tmp_path)
    rid = str(uuid.uuid4())
    legacy = session_store.EVALUATION_DIR / f"{rid}_session.json"
    legacy.write_text(
        json.dumps({"portal_id": 1, "run_id": rid}),
        encoding="utf-8",
    )
    loaded = load_session_json(rid)
    assert loaded is not None
    assert loaded.get("portal_id") == 1
