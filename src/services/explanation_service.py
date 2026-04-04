"""Optional LLM-backed explanations for learning plans."""

from __future__ import annotations

from typing import Any, Sequence

from llm.llm_client import LlmClient
from llm.prompts import build_plan_explanation_prompt
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def build_deterministic_explanation(
    practice: str | None,
    target_expertise: str | None,
    course_names: Sequence[str],
    planned_hours: float,
    remaining_gap: float,
) -> str:
    """Create a short explanation without calling an LLM.

    Args:
        practice: Employee practice.
        target_expertise: Optional focus area.
        course_names: Recommended course titles.
        planned_hours: Sum of planned hours.
        remaining_gap: Hours remaining toward goal after plan.

    Returns:
        Plain-text explanation.
    """
    focus = target_expertise or "mapped practice skills"
    pr = practice or "the employee practice"
    names = ", ".join(course_names[:8])
    if len(course_names) > 8:
        names += ", ..."
    return (
        f"Planned {planned_hours:.1f} hours toward the annual goal using courses aligned with "
        f"{pr} and {focus}. Recommended: {names}. "
        f"Remaining gap after this plan: {remaining_gap:.1f} hours."
    )


class ExplanationService:
    """Generate grounded explanations when an API key is configured."""

    def __init__(self, client: LlmClient | None = None) -> None:
        """Initialize with optional LLM client."""
        self._client = client or LlmClient()

    def explain_plan(
        self,
        *,
        include_llm: bool,
        employee_context: dict[str, Any],
        recommended: list[dict[str, Any]],
        retrieved_context_chunks: list[str],
    ) -> str:
        """Produce plan explanation, using LLM only when enabled and available.

        Args:
            include_llm: Whether to attempt an LLM call.
            employee_context: Serialized employee fields.
            recommended: Recommendation objects from plan builder.
            retrieved_context_chunks: Course text snippets used as grounding.

        Returns:
            Explanation string.
        """
        names = [str(r.get("course_name", "")) for r in recommended]
        practice = employee_context.get("practice")
        expertise = employee_context.get("target_expertise")
        planned = float(employee_context.get("planned_hours", 0.0) or 0.0)
        gap = float(employee_context.get("remaining_gap_after_plan", 0.0) or 0.0)
        if not include_llm or not self._client.is_configured():
            return build_deterministic_explanation(practice, expertise, names, planned, gap)
        prompt = build_plan_explanation_prompt(employee_context, recommended, retrieved_context_chunks)
        try:
            return self._client.complete(prompt).strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM explanation failed, using deterministic text: %s", exc)
            return build_deterministic_explanation(practice, expertise, names, planned, gap)
