"""FastAPI route definitions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from api.schemas import GeneratePlanRequest, GeneratePlanResponse, HealthResponse
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
    """Generate a personalized learning plan for an employee."""
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
    return GeneratePlanResponse(**payload)
