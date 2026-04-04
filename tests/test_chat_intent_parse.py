"""Tests for natural-language plan intent parsing."""

from __future__ import annotations

from utils.chat_intent_parse import (
    explain_portal_resolution_failure,
    parse_learning_plan_intent,
    resolve_portal_id,
)


def test_explicit_portal_and_expertise() -> None:
    intent = parse_learning_plan_intent(
        "Please plan for portal id 24463, focus on Java.",
    )
    assert intent.explicit_portal_id == 24463
    assert intent.target_expertise and "java" in intent.target_expertise.lower()


def test_resolve_first_matching_int_in_valid_set() -> None:
    intent = parse_learning_plan_intent("Need training 99999 and backup 42 for next year")
    valid = {42, 100}
    assert resolve_portal_id(intent, valid) == 42


def test_explicit_portal_preferred() -> None:
    intent = parse_learning_plan_intent("User id 10 but also mention 99")
    valid = {10, 99}
    assert resolve_portal_id(intent, valid) == 10


def test_explain_failure() -> None:
    intent = parse_learning_plan_intent("hello")
    assert "portal id" in explain_portal_resolution_failure(intent).lower()
