"""Tests for RAGAS metric wiring (no live API calls)."""

from __future__ import annotations

import pytest

from evaluation.ragas_metrics import compute_ragas_scores


def _minimal_session() -> dict:
    return {
        "run_id": "00000000-0000-4000-8000-000000000099",
        "portal_id": 1,
        "ragas_evaluation_inputs": {
            "question": "What to learn?",
            "answer": "Course A and B.",
            "contexts": ["Course A covers X."],
        },
    }


def test_compute_ragas_scores_errors_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    out = compute_ragas_scores(_minimal_session())
    assert out.get("error")
    assert "OPENAI_API_KEY" in out["error"] or "AZURE_OPENAI_API_KEY" in out["error"]
