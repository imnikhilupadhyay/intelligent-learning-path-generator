"""End-to-end learning plan generation (deterministic core + optional LLM)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from planning.hour_optimizer import select_courses_for_hours, sum_hours
from planning.plan_builder import attach_prereq_metadata, build_recommendation_items
from planning.prerequisite_resolver import build_ordered_ids_with_prereqs
from planning.ranking_engine import compute_scores, top_n
from services.completion_service import CompletionService
from services.course_service import CourseService
from services.explanation_service import ExplanationService
from services.practice_mapper import skills_for_practice
from services.retrieval_service import RetrievalService
from services.user_service import UserService
from utils.constants import COL_COURSE_ID, COL_COURSE_FULL_NAME, COL_SUMMARY
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def build_employee_intro_markdown(
    employee_name: str | None,
    portal_id: int,
    practice: str | None,
    target_expertise: str | None,
) -> str:
    """Build greeting and employee context as short markdown paragraphs.

    Args:
        employee_name: Name from user master, if present.
        portal_id: Resolved portal identifier.
        practice: Employee practice (e.g. Application Services).
        target_expertise: Optional focus area for this plan.

    Returns:
        Markdown string shown at the top of plan responses.
    """
    name = (employee_name or "").strip()
    practice_display = (practice or "").strip()
    parts: list[str] = []
    if name:
        parts.append(f"Hello, **{name}**.")
    else:
        parts.append("Hello.")
    if practice_display:
        parts.append(
            f"Your **portal id** is **{portal_id}**. "
            f"You belong to the employee practice **{practice_display}**.",
        )
    else:
        parts.append(
            f"Your **portal id** is **{portal_id}**. "
            "Employee practice was not listed in your profile.",
        )
    if target_expertise:
        te = str(target_expertise).strip()
        if te:
            parts.append(f"For this plan, your focus is **{te}**.")
    return "\n\n".join(parts)


def build_ragas_evaluation_inputs(
    portal_id: int,
    target_expertise: str | None,
    explanation: str | None,
    recommended: list[dict[str, Any]],
    context_chunks: list[str],
) -> dict[str, Any]:
    """Build question/answer/contexts for RAG-style evaluation (e.g. RAGAS).

    Args:
        portal_id: Employee portal id.
        target_expertise: Optional user focus.
        explanation: Optional LLM/deterministic explanation text.
        recommended: Recommendation dicts from the plan.
        context_chunks: Course title+summary snippets used for grounding.

    Returns:
        Mapping with ``question``, ``answer``, and ``contexts`` (list of str).
    """
    q = f"What learning courses should be recommended for portal id {portal_id}"
    if target_expertise and str(target_expertise).strip():
        q += f", with emphasis on {str(target_expertise).strip()}"
    q += "?"
    lines: list[str] = []
    for r in recommended:
        nm = str(r.get("course_name", "") or "")
        cid = r.get("course_id", "")
        reason = str(r.get("reason", "") or "")
        lines.append(f"{nm} (id {cid}): {reason}")
    recap = "\n".join(lines) if lines else "No courses recommended."
    parts_a: list[str] = []
    if explanation and str(explanation).strip():
        parts_a.append(str(explanation).strip())
    parts_a.append("Plan summary:\n" + recap)
    answer = "\n\n".join(parts_a)
    ctx = list(context_chunks) if context_chunks else ["(No course context snippets.)"]
    return {"question": q, "answer": answer, "contexts": ctx}


class LearningPlanOrchestrator:
    """Coordinates services and planning to produce API responses."""

    def __init__(
        self,
        user_service: UserService | None = None,
        completion_service: CompletionService | None = None,
        course_service: CourseService | None = None,
        retrieval_service: RetrievalService | None = None,
        explanation_service: ExplanationService | None = None,
    ) -> None:
        """Wire default services."""
        self.users = user_service or UserService()
        self.completions = completion_service or CompletionService()
        self.courses = course_service or CourseService()
        self.retrieval = retrieval_service or RetrievalService()
        self.explanations = explanation_service or ExplanationService()

    def generate_plan(
        self,
        portal_id: int,
        target_expertise: str | None,
        top_k: int,
        include_explanation: bool,
        include_optional_courses: bool = False,
    ) -> dict[str, Any]:
        """Build full plan payload for an employee.

        Args:
            portal_id: Employee portal id.
            target_expertise: Optional expertise focus.
            top_k: Retrieval / ranking breadth.
            include_explanation: Whether to attach natural-language explanation.
            include_optional_courses: When True, add extra ranked courses beyond the
                minimum needed for the annual hour target (supplemental recommendations).

        Returns:
            Serializable response dict aligned with API schema.

        Raises:
            ValueError: If employee is not found.
        """
        profile = self.users.get_by_portal_id(portal_id)
        if profile is None:
            raise ValueError(f"Employee not found for portal_id={portal_id}")

        completed = self.completions.completed_course_ids(portal_id)
        df_all = self.courses.load_enriched()
        if df_all.empty:
            raise ValueError("Course catalog is empty; run ingestion pipeline first.")

        candidate_ids, sem_map = self.retrieval.hybrid_retrieve(
            df_all,
            profile.practice,
            target_expertise,
            top_k=top_k,
        )
        if not candidate_ids:
            candidate_ids = [
                int(float(x))
                for x in df_all[COL_COURSE_ID].tolist()
                if str(x) not in ("nan", "None", "")
            ][: max(top_k * 3, 20)]

        id_set = set()
        clean_candidates: list[int] = []
        for cid in candidate_ids:
            if cid in id_set:
                continue
            id_set.add(cid)
            clean_candidates.append(cid)

        mask = df_all[COL_COURSE_ID].apply(lambda x: int(float(x)) in clean_candidates)
        cand_df = df_all[mask].copy()
        cand_df = cand_df[~cand_df[COL_COURSE_ID].apply(lambda x: int(float(x)) in completed)]

        skills = skills_for_practice(profile.practice)
        ranked = compute_scores(
            cand_df,
            practice_keywords=skills,
            target_expertise=target_expertise,
            semantic_scores=sem_map,
            employee_grade=profile.grade,
            completed_ids=completed,
        )
        ranked_top = top_n(ranked, n=max(top_k, 5))

        prereq_map = attach_prereq_metadata(df_all)
        ordered_ids = [int(float(x)) for x in ranked_top[COL_COURSE_ID].tolist()]
        ordered_ids = build_ordered_ids_with_prereqs(ordered_ids, prereq_map, completed)

        hours_map: dict[int, float] = {}
        for _, row in df_all.iterrows():
            try:
                cid = int(float(row.get(COL_COURSE_ID)))
            except (TypeError, ValueError):
                continue
            try:
                h = float(row.get("parsed_duration_hours", 2.0))
            except (TypeError, ValueError):
                h = 2.0
            hours_map[cid] = h

        goal = profile.annual_training_goal_hours or 0.0
        completed_hours = sum_hours(completed, hours_map)
        try:
            remaining = max(0.0, float(goal) - float(completed_hours))
        except (TypeError, ValueError):
            remaining = float(goal or 0.0)

        hour_result = select_courses_for_hours(
            ordered_ids,
            hours_map,
            remaining,
            allow_overshoot_hours=12.0 if include_optional_courses else 2.0,
        )
        selected_ids = list(hour_result.selected_course_ids)
        if include_optional_courses and ordered_ids:
            extra_cap = min(24.0, max(6.0, float(remaining) * 0.5))
            extra_hours = 0.0
            max_extra = 5
            extras = 0
            for cid in ordered_ids:
                if cid in selected_ids:
                    continue
                if extras >= max_extra or extra_hours >= extra_cap:
                    break
                h = float(hours_map.get(cid, 2.0))
                selected_ids.append(cid)
                extra_hours += h
                extras += 1

        reasons: dict[int, str] = {}
        for _, row in ranked_top.iterrows():
            try:
                cid = int(float(row.get(COL_COURSE_ID)))
            except (TypeError, ValueError):
                continue
            pm = float(row.get("practice_match_score", 0.0))
            reasons[cid] = (
                f"Practice relevance {pm:.2f}; fits remaining {remaining:.1f}h target planning."
            )
        if include_optional_courses:
            base_set = set(hour_result.selected_course_ids)
            for cid in selected_ids:
                if cid in base_set:
                    continue
                reasons.setdefault(
                    cid,
                    "Optional supplement beyond the minimum hours for your goal.",
                )

        recs = build_recommendation_items(selected_ids, df_all, reasons)

        planned = sum(float(hours_map.get(int(c), 2.0)) for c in selected_ids)
        planned = round(planned, 2)
        gap = max(0.0, float(goal) - float(completed_hours) - planned)

        context_chunks: list[str] = []
        for cid in selected_ids[:10]:
            row = df_all[df_all[COL_COURSE_ID].astype(str) == str(cid)]
            if not row.empty:
                r = row.iloc[0]
                context_chunks.append(
                    f"{r.get(COL_COURSE_FULL_NAME, '')}: {r.get(COL_SUMMARY, '')}",
                )

        employee_context = {
            "portal_id": profile.portal_id,
            "practice": profile.practice,
            "target_expertise": target_expertise,
            "annual_training_goal_hours": goal,
            "planned_hours": planned,
            "remaining_gap_after_plan": gap,
        }
        explanation = self.explanations.explain_plan(
            include_llm=include_explanation,
            employee_context=employee_context,
            recommended=recs,
            retrieved_context_chunks=context_chunks,
        )

        return {
            "portal_id": portal_id,
            "employee_name": profile.employee_name,
            "employee_intro": build_employee_intro_markdown(
                profile.employee_name,
                portal_id,
                profile.practice,
                target_expertise,
            ),
            "grade": profile.grade,
            "practice": profile.practice,
            "target_expertise": target_expertise,
            "annual_training_goal_hours": goal,
            "completed_course_ids": sorted(completed),
            "completed_hours": completed_hours,
            "remaining_target_hours": remaining,
            "skills_used_for_retrieval": skills,
            "recommended_courses": recs,
            "planned_hours": planned,
            "remaining_gap_after_plan": gap,
            "explanation": explanation.strip() or None,
            "ragas_evaluation_inputs": build_ragas_evaluation_inputs(
                portal_id,
                target_expertise,
                explanation.strip() or None,
                recs,
                context_chunks,
            ),
            "warnings": hour_result.warnings
            + (
                ["Optional courses were added beyond the strict hour target."]
                if include_optional_courses and len(selected_ids) > len(hour_result.selected_course_ids)
                else []
            ),
        }
