"""Enterprise HTTP boundary around the framework-neutral Research Core."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from src.application.research import ProjectNotFoundError, ResearchApplication
from src.core.container import ServiceContainer
from src.persistence.factory import create_project_repository
from src.services.reviewer_orchestration import ReviewerPipelineError
from src.state.project import (
    ProjectState,
    ResearchMode,
    ResearchPath,
    WorkspaceMode,
)


class ProjectCreate(BaseModel):
    project_name: str
    industry: str
    region: str
    research_objective: str
    time_horizon: str
    output_language: str = "简体中文"
    target_company: str | None = None
    company_strategy_enabled: bool = False
    company_strategy_objective: str | None = None
    decision_context: str | None = None
    research_mode: ResearchMode = ResearchMode.GENERAL
    workspace_mode: WorkspaceMode = WorkspaceMode.QUICK_REPORT
    research_path: ResearchPath = ResearchPath.BUILD_FIRST
    industry_pack: str | None = None


class PipelineRequest(BaseModel):
    enterprise: bool | None = None


class ProjectScopeUpdate(BaseModel):
    """Editable scope fields shared by both research presentation paths."""

    project_name: str
    industry: str
    region: str
    research_objective: str
    time_horizon: str
    output_language: str = "简体中文"
    target_company: str | None = None
    company_strategy_objective: str | None = None
    confirm: bool = False

    @field_validator(
        "project_name",
        "industry",
        "region",
        "research_objective",
        "time_horizon",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("required scope fields cannot be empty")
        return cleaned


@lru_cache(maxsize=1)
def build_application() -> ResearchApplication:
    return ResearchApplication(
        projects=create_project_repository(),
        service_factory=ServiceContainer.from_runtime,
    )

app = FastAPI(
    title="Trident Research API",
    version="0.2.0",
    description="Enterprise research and strategic decision intelligence",
)


def get_research_application() -> ResearchApplication:
    return build_application()


ResearchApp = Annotated[ResearchApplication, Depends(get_research_application)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "trident-research-api"}


@app.get("/ready", response_model=None)
def readiness():
    """Report whether the configured persistence service can accept traffic."""
    try:
        research = build_application()
        research.check_persistence()
    except Exception as exc:  # readiness must remain observable during outages
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "service": "trident-research-api",
                "reason": type(exc).__name__,
            },
        )
    return {"status": "ready", "service": "trident-research-api"}


@app.get("/v1/capabilities")
def capabilities(research: ResearchApp) -> dict:
    registries = {
        "scenario_packs": research.services.scenario_packs,
        "industry_packs": research.services.industry_packs,
        "algorithms": research.services.algorithms,
        "evaluators": research.services.evaluators,
    }
    return {
        "delivery_channels": ["streamlit-compatibility", "fastapi"],
        "research_paths": ["research-build-first", "report-review-first"],
        "services": [
            "research-planning",
            "evidence-collection",
            "industry-analysis",
            "future-intelligence",
            "report-generation",
            "company-scorecard",
            "action-plan",
        ],
        "extensions": {
            name: [
                {
                    "extension_id": item.extension_id,
                    "version": item.version,
                    "display_name": item.display_name,
                    "description": item.description,
                    "capabilities": item.capabilities,
                }
                for item in registry.descriptors()
            ]
            for name, registry in registries.items()
        },
    }


@app.post("/v1/projects", response_model=ProjectState, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, research: ResearchApp) -> ProjectState:
    return research.create_project(ProjectState(**payload.model_dump()))


@app.get("/v1/projects", response_model=list[ProjectState])
def list_projects(
    research: ResearchApp,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProjectState]:
    return research.list_projects(limit=limit, offset=offset)


@app.get("/v1/projects/{project_id}", response_model=ProjectState)
def get_project(project_id: str, research: ResearchApp) -> ProjectState:
    try:
        return research.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc


@app.patch("/v1/projects/{project_id}/scope", response_model=ProjectState)
def update_project_scope(
    project_id: str, payload: ProjectScopeUpdate, research: ResearchApp
) -> ProjectState:
    try:
        return research.update_scope(
            project_id,
            scope=payload.model_dump(exclude={"confirm"}),
            confirm=payload.confirm,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc


@app.put("/v1/projects/{project_id}", response_model=ProjectState)
def replace_project(
    project_id: str, payload: ProjectState, research: ResearchApp
) -> ProjectState:
    if payload.project_id != project_id:
        raise HTTPException(status_code=409, detail="project id mismatch")
    try:
        return research.save_project(payload)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc


@app.delete("/v1/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, research: ResearchApp) -> None:
    if not research.delete_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")


@app.post("/v1/projects/{project_id}/research-brief", response_model=ProjectState)
def generate_research_brief(project_id: str, research: ResearchApp) -> ProjectState:
    try:
        return research.generate_brief(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc


@app.post("/v1/projects/{project_id}/report-first", response_model=ProjectState)
async def run_report_first(
    project_id: str, payload: PipelineRequest, research: ResearchApp
) -> ProjectState:
    try:
        return await research.run_report_first(project_id, enterprise=payload.enterprise)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ReviewerPipelineError as exc:
        research.projects.save(exc.project)
        raise HTTPException(
            status_code=422,
            detail={"stage": exc.stage, "message": str(exc)},
        ) from exc
