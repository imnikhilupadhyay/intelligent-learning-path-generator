"""Prompt templates for optional LLM calls."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence


def build_plan_explanation_prompt(
    employee_context: Mapping[str, Any],
    recommended: Sequence[Mapping[str, Any]],
    retrieved_context_chunks: Sequence[str],
) -> str:
    """Build a grounded explanation prompt for the learning plan.

    Args:
        employee_context: Employee fields (practice, goal, etc.).
        recommended: Recommended course dicts.
        retrieved_context_chunks: Snippets from course summaries / retrieval.

    Returns:
        Prompt text for the chat model.
    """
    ctx = json.dumps(employee_context, ensure_ascii=False, indent=2)
    rec = json.dumps(list(recommended), ensure_ascii=False, indent=2)
    chunks = "\n---\n".join(retrieved_context_chunks[:20])
    return (
        "You are an enterprise learning advisor. Explain why the recommended courses fit "
        "the employee context. Use ONLY facts supported by the CONTEXT snippets and course list. "
        "Do not invent prerequisites or durations. Keep under 180 words.\n\n"
        f"EMPLOYEE_CONTEXT:\n{ctx}\n\nRECOMMENDED:\n{rec}\n\nCONTEXT:\n{chunks}\n"
    )


def build_metadata_extraction_prompt(summary: str) -> str:
    """Prompt the model to extract structured fields from a messy summary.

    Args:
        summary: Raw course summary.

    Returns:
        Prompt requesting JSON only output.
    """
    return (
        "Extract fields from the course summary. Return JSON ONLY with keys: "
        "duration_hours (number|null), prerequisite (string|null), audience (string|null), "
        "grade_hint (string|null). Use null if unknown. Do not guess.\n\n"
        f"SUMMARY:\n{summary}\n"
    )
