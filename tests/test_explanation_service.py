"""Explanation service behavior."""

from __future__ import annotations

import pytest

from services.explanation_service import ExplanationService


def test_no_explanation_when_not_requested() -> None:
    """Checkbox off should not synthesize deterministic explanation text."""
    svc = ExplanationService()
    out = svc.explain_plan(
        include_llm=False,
        employee_context={},
        recommended=[],
        retrieved_context_chunks=[],
    )
    assert out == ""


def test_deterministic_when_requested_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """When explanation requested but no key, fall back to deterministic text."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    svc = ExplanationService()
    out = svc.explain_plan(
        include_llm=True,
        employee_context={
            "practice": "BPS",
            "target_expertise": None,
            "planned_hours": 2.0,
            "remaining_gap_after_plan": 1.0,
        },
        recommended=[{"course_name": "Foo"}],
        retrieved_context_chunks=[],
    )
    assert "Planned" in out
    assert "BPS" in out
