"""Tests for plan run_id persistence on the generate-plan route."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import evaluation.session_store as session_store


@pytest.fixture
def session_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Redirect evaluation paths under tmp_path."""
    ev = tmp_path / "eval"
    run_ids = ev / "run_ids"
    session_runs = ev / "session_runs"
    run_ids.mkdir(parents=True)
    monkeypatch.setattr(session_store, "EVALUATION_DIR", ev)
    monkeypatch.setattr(session_store, "EVALUATION_RUN_IDS_DIR", run_ids)
    monkeypatch.setattr(session_store, "EVALUATION_SESSION_CSV", run_ids / "session.csv")
    monkeypatch.setattr(session_store, "EVALUATION_SESSION_RUNS_DIR", session_runs)
    return ev, run_ids


def _fake_plan_payload(portal_id: int = 1) -> dict:
    return {
        "portal_id": portal_id,
        "employee_name": "Test",
        "employee_intro": "Hello",
        "grade": None,
        "practice": "Practice",
        "target_expertise": None,
        "annual_training_goal_hours": 40.0,
        "completed_course_ids": [],
        "completed_hours": 0.0,
        "remaining_target_hours": 40.0,
        "skills_used_for_retrieval": ["skill"],
        "recommended_courses": [],
        "planned_hours": 2.0,
        "remaining_gap_after_plan": 38.0,
        "explanation": None,
        "ragas_evaluation_inputs": {
            "question": "q?",
            "answer": "a",
            "contexts": ["c1"],
        },
        "warnings": [],
    }


def test_generate_plan_returns_run_id_and_writes_json(
    session_dirs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_orch = MagicMock()
    mock_orch.generate_plan.return_value = _fake_plan_payload(1)
    monkeypatch.setattr("api.routes._orchestrator", mock_orch)

    from api.main import app

    client = TestClient(app)
    r = client.post(
        "/generate-plan",
        json={"portal_id": 1, "include_explanation": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert "run_id" in body
    rid = body["run_id"]
    assert body["ragas_evaluation_inputs"]["question"] == "q?"
    loaded = session_store.load_session_json(rid)
    assert loaded is not None
    assert loaded.get("portal_id") == 1
    assert loaded.get("run_id") == rid


def test_generate_plan_reuses_session_run_id(
    session_dirs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_orch = MagicMock()
    mock_orch.generate_plan.return_value = _fake_plan_payload(1)
    monkeypatch.setattr("api.routes._orchestrator", mock_orch)

    from api.main import app

    client = TestClient(app)
    first = client.post("/generate-plan", json={"portal_id": 1}).json()
    rid = first["run_id"]

    second = client.post(
        "/generate-plan",
        json={"portal_id": 1, "session_run_id": rid},
    ).json()
    assert second["run_id"] == rid


def test_ragas_metrics_404_for_unknown_run(
    session_dirs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_orch = MagicMock()
    mock_orch.generate_plan.return_value = _fake_plan_payload(1)
    monkeypatch.setattr("api.routes._orchestrator", mock_orch)

    from api.main import app

    client = TestClient(app)
    fake_uuid = "00000000-0000-4000-8000-000000000001"
    r = client.get(f"/evaluation/ragas-metrics/{fake_uuid}")
    assert r.status_code == 404
