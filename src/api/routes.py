"""FastAPI route definitions."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from api.schemas import (
    GeneratePlanRequest,
    GeneratePlanResponse,
    HealthResponse,
    RagasMetricsResponse,
)
from evaluation.ragas_metrics import compute_ragas_scores
from evaluation.session_store import (
    append_session_csv_row,
    is_valid_run_id,
    load_session_json,
    resolve_run_id,
    write_session_json,
)
from services.learning_plan_orchestrator import LearningPlanOrchestrator
from utils.constants import get_retrieval_top_k

router = APIRouter()
_orchestrator = LearningPlanOrchestrator()


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """No HTML landing page; Swagger UI is the friendly entry for ``/``."""
    return RedirectResponse(url="/docs")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse()


@router.post("/generate-plan", response_model=GeneratePlanResponse)
def generate_plan(body: GeneratePlanRequest) -> GeneratePlanResponse:
    """Generate a personalized learning plan for an employee.

    Returns ``run_id`` and persists ``session_runs/<run_id>_session.json``. Omit
    ``session_run_id`` until you have a prior ``run_id`` from this endpoint.
    Evaluation metrics are separate routes under ``/evaluation/`` (e.g. RAGAS).
    """
    try:
        payload = _orchestrator.generate_plan(
            portal_id=body.portal_id,
            target_expertise=body.target_expertise,
            top_k=get_retrieval_top_k(),
            include_explanation=body.include_explanation,
            include_optional_courses=body.include_optional_courses,
        )
    except ValueError as exc:
        detail = str(exc)
        code = 404 if "Employee not found" in detail or "not found for portal_id" in detail else 400
        raise HTTPException(status_code=code, detail=detail) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Data file missing: {exc}") from exc

    run_id, is_new_run = resolve_run_id(body.portal_id, body.session_run_id)
    ts = datetime.now(timezone.utc).isoformat()
    if is_new_run:
        append_session_csv_row(run_id, body.portal_id, ts)
    stored = {**payload, "run_id": run_id}
    write_session_json(run_id, stored)
    out = {**payload, "run_id": run_id}
    return GeneratePlanResponse(**out)


@router.get("/evaluation/ragas-metrics/{run_id}", response_model=RagasMetricsResponse)
def ragas_metrics(run_id: str) -> RagasMetricsResponse:
    """Compute RAGAS scores for a saved plan run (requires ``OPENAI_API_KEY`` on the API host).

    Decoupled from ``POST /generate-plan`` so additional eval endpoints can follow
    the same pattern without changing the plan request/response shape.
    """
    if not is_valid_run_id(run_id):
        raise HTTPException(status_code=400, detail="Invalid run_id; expected a UUID string.")
    session = load_session_json(run_id.strip())
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"No saved session for run_id={run_id!r} (generate a plan first).",
        )
    result = compute_ragas_scores(session)
    return RagasMetricsResponse(
        run_id=result.get("run_id"),
        portal_id=result.get("portal_id"),
        scores=result.get("scores") or {},
        metric_descriptions=result.get("metric_descriptions") or {},
        error=result.get("error"),
    )
