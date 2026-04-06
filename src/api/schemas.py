"""Pydantic request/response models for the FastAPI layer."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GeneratePlanRequest(BaseModel):
    """Input payload for ``POST /generate-plan``."""

    portal_id: int = Field(..., description="Employee portal identifier")
    target_expertise: str | None = Field(default=None, description="Optional expertise focus")
    include_explanation: bool = Field(default=False, description="Request LLM explanation when configured")
    include_optional_courses: bool = Field(
        default=False,
        description="Add supplemental courses beyond the minimum hour target",
    )
    session_run_id: str | None = Field(
        default=None,
        description=(
            "Optional UUID from a prior plan in the same client session; "
            "server reuses it only if the stored session exists and portal_id matches."
        ),
    )


class RecommendedCourse(BaseModel):
    """Single recommended course entry."""

    course_id: int
    course_name: str
    hours: float
    prerequisite: str | None = None
    reason: str


class GeneratePlanResponse(BaseModel):
    """Learning plan response aligned with workflow examples."""

    portal_id: int
    employee_name: str | None = None
    employee_intro: str = Field(
        ...,
        description=(
            "Greeting and employee context: name, portal id wording, practice, optional focus"
        ),
    )
    grade: float | None = None
    practice: str | None = None
    target_expertise: str | None = None
    annual_training_goal_hours: float | None = None
    completed_course_ids: list[int]
    completed_hours: float
    remaining_target_hours: float
    skills_used_for_retrieval: list[str]
    recommended_courses: list[dict[str, Any]]
    planned_hours: float
    remaining_gap_after_plan: float
    explanation: str | None = None
    warnings: list[str] = Field(default_factory=list)
    run_id: str = Field(..., description="UUID for this plan run (session logging / RAGAS lookup)")
    ragas_evaluation_inputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Question, answer, and contexts for RAG-style evaluation (e.g. RAGAS)",
    )


class RagasMetricsResponse(BaseModel):
    """JSON body for ``GET /evaluation/ragas-metrics/{run_id}``."""

    run_id: str | None = None
    portal_id: int | None = None
    scores: dict[str, float] = Field(default_factory=dict)
    metric_descriptions: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


class HealthResponse(BaseModel):
    """Health check body."""

    status: str = "ok"
