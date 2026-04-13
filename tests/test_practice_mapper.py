"""Practice mapping tests."""

from __future__ import annotations

from services.practice_mapper import build_retrieval_query_phrase, normalize_practice, skills_for_practice


def test_normalize_application_services() -> None:
    """Alias maps to canonical practice label."""
    assert normalize_practice("application services") == "Application Services"


def test_skills_not_empty_for_cloud() -> None:
    """Cloud practice returns keyword skills from YAML."""
    skills = skills_for_practice("Cloud & Security")
    assert "cloud" in [s.lower() for s in skills]


def test_retrieval_query_contains_expertise() -> None:
    """Target expertise appears in composed query."""
    q = build_retrieval_query_phrase("Global Support", "ServiceNow")
    assert "servicenow" in q.lower()
