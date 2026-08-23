"""Enterprise HTTP boundary around the framework-neutral Research Core."""

from __future__ import annotations

from functools import lru_cache
from datetime import UTC, datetime
import os
import secrets
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from src.application.research import (
    ProjectNotFoundError,
    ResearchApplication,
    ResearchWorkflowError,
)
from src.config import ConfigurationError
from src.core.container import ServiceContainer
from src.models.research import MarketDefinition
from src.models.evidence import EvidenceReviewStatus
from src.models.analysis import AnalysisReviewStatus
from src.models.future import ForecastReviewStatus
from src.models.strategy import StrategyReviewStatus
from src.persistence.factory import create_project_repository
from src.providers.base import ProviderError
from src.core.registry import ExtensionRegistry
from src.integrations import builtin_integration_surfaces
from src.scenarios import (
    ScenarioContractError,
    ScenarioInputError,
    ScenarioWorkflowRunner,
    builtin_scenario_packs,
)
from src.services.research_planning import SOPComplianceError
from src.services.industry_analysis import IndustryAnalysisError
from src.services.errors import FutureIntelligenceError
from src.services.report_generation import ReportGenerationError
from src.services.evidence_collection import EvidenceCollectionError
from src.services.reviewer_orchestration import ReviewerPipelineError
from src.services.company_assessment import CompanyAssessmentError
from src.services.action_planning import ActionPlanningError
from src.services.scenario_interview import ScenarioInterviewError, ScenarioInterviewService
from src.services.research_routing import ScenarioResearchRouter
from src.state.project import (
    ProjectState,
    ResearchMode,
    ResearchPath,
    WorkspaceMode,
    rewind_to_previous_review_gate,
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
    scenario_pack: str = "general"
    scenario_pack_version: str = "1.0.0"


SCENARIO_PACKS = ExtensionRegistry(builtin_scenario_packs())
SCENARIO_WORKFLOW = ScenarioWorkflowRunner(SCENARIO_PACKS)
SCENARIO_INTERVIEWS = ScenarioInterviewService(
    SCENARIO_PACKS,
    model_factory=lambda: ServiceContainer.from_runtime()._model(),
)
SCENARIO_ROUTER = ScenarioResearchRouter(SCENARIO_PACKS)


class InterviewStartRequest(BaseModel):
    restart: bool = False


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(min_length=1)


class ResearchRouteRequest(BaseModel):
    available_materials: list[str] = Field(default_factory=list)
    has_existing_report: bool = False


class ProfileReviewRequest(BaseModel):
    operating_portrait: str
    decision_style: str
    research_next_step: str
    confirm: bool = False


class PipelineRequest(BaseModel):
    enterprise: bool | None = None
    background: bool = False


class StrategyReviewDecision(BaseModel):
    item_id: str
    status: StrategyReviewStatus
    note: str | None = None


class StrategyReviewRequest(BaseModel):
    decisions: list[StrategyReviewDecision] = Field(default_factory=list)
    confirm: bool = False


class ActionFeedbackRequest(BaseModel):
    action_id: str = Field(min_length=1)
    progress_pct: int = Field(ge=0, le=100)
    outcome_metrics: str = ""
    blockers: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    scenario_fields: dict[str, str] = Field(default_factory=dict)


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


class ResearchBriefReview(BaseModel):
    decision_statement: str
    market_definition: MarketDefinition
    key_questions: list[str] = Field(min_length=1)
    information_gaps: list[str] = Field(min_length=1)
    hypotheses: list[str] = Field(min_length=1)
    clarification_questions: list[str] = Field(default_factory=list)
    clarification_responses: dict[str, str] = Field(default_factory=dict)
    confidence_note: str
    confirm: bool = False


class PlanConfirmation(BaseModel):
    confirm: bool = True


class EvidenceCollectionRequest(BaseModel):
    task_ids: list[str] | None = None
    query_override: str | None = None


class EvidenceDecision(BaseModel):
    evidence_id: str
    status: EvidenceReviewStatus
    note: str | None = None

    @field_validator("status")
    @classmethod
    def require_human_decision(cls, value: EvidenceReviewStatus) -> EvidenceReviewStatus:
        if value not in {EvidenceReviewStatus.ACCEPTED, EvidenceReviewStatus.REJECTED}:
            raise ValueError("evidence decision must be accepted or rejected")
        return value


class EvidenceReviewRequest(BaseModel):
    decisions: list[EvidenceDecision] = Field(default_factory=list)
    confirm: bool = False
    coverage_gap_resolution: str | None = None
    coverage_gap_user_input: str | None = None
    coverage_gaps_acknowledged: bool = False


class AnalysisDecision(BaseModel):
    finding_id: str
    status: AnalysisReviewStatus
    note: str | None = None

    @field_validator("status")
    @classmethod
    def require_human_decision(cls, value: AnalysisReviewStatus) -> AnalysisReviewStatus:
        if value not in {AnalysisReviewStatus.ACCEPTED, AnalysisReviewStatus.REJECTED}:
            raise ValueError("analysis decision must be accepted or rejected")
        return value


class IndustryAnalysisReviewRequest(BaseModel):
    decisions: list[AnalysisDecision] = Field(default_factory=list)
    confirm: bool = False


class ForecastDecision(BaseModel):
    item_id: str
    status: ForecastReviewStatus
    note: str | None = None

    @field_validator("status")
    @classmethod
    def require_human_decision(cls, value: ForecastReviewStatus) -> ForecastReviewStatus:
        if value not in {ForecastReviewStatus.ACCEPTED, ForecastReviewStatus.REJECTED}:
            raise ValueError("forecast decision must be accepted or rejected")
        return value


class FutureIntelligenceReviewRequest(BaseModel):
    decisions: list[ForecastDecision] = Field(default_factory=list)
    confirm: bool = False


class WorkflowRewindResponse(BaseModel):
    project: ProjectState
    message: str


@lru_cache(maxsize=1)
def build_application() -> ResearchApplication:
    return ResearchApplication(
        projects=create_project_repository(),
        service_factory=ServiceContainer.from_runtime,
    )

app = FastAPI(
    title="Trident Research API",
    version="0.3.0",
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


def _require_ops_access(
    x_trident_ops_key: Annotated[str | None, Header()] = None,
) -> None:
    expected = os.getenv("TRIDENT_OPS_KEY", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="运营后台尚未配置访问密钥")
    if not x_trident_ops_key or not secrets.compare_digest(
        x_trident_ops_key, expected
    ):
        raise HTTPException(status_code=401, detail="运营后台访问凭证无效")


@app.get("/v1/ops/telemetry", dependencies=[Depends(_require_ops_access)])
def ops_telemetry(research: ResearchApp) -> dict:
    """Return privacy-safe, source-backed telemetry for the internal dashboard."""

    projects = research.list_projects(limit=500)
    rows = [
        {
            **run.model_dump(mode="json"),
            "project_name": project.project_name,
            "industry": project.industry,
            "region": project.region,
            "report_completed": project.general_report_artifact is not None,
        }
        for project in projects
        for run in project.telemetry_runs
    ]
    total_tokens = sum(int(row["total_tokens"]) for row in rows)
    completed_reports = sum(
        project.general_report_artifact is not None for project in projects
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "ProjectState.telemetry_runs / provider-reported usage",
        "coverage_started_at": min(
            (row["started_at"] for row in rows), default=None
        ),
        "summary": {
            "project_count": len(projects),
            "completed_report_count": completed_reports,
            "step_run_count": len(rows),
            "failed_step_count": sum(row["status"] == "failed" for row in rows),
            "model_call_count": sum(len(row["model_calls"]) for row in rows),
            "total_tokens": total_tokens,
            "average_tokens_per_completed_report": (
                round(total_tokens / completed_reports) if completed_reports else None
            ),
        },
        "runs": sorted(rows, key=lambda row: row["started_at"], reverse=True),
    }


@app.get("/v1/capabilities")
def capabilities() -> dict:
    registries = {
        "scenario_packs": SCENARIO_PACKS,
        "industry_packs": ExtensionRegistry(),
        "algorithms": ExtensionRegistry(),
        "evaluators": ExtensionRegistry(),
    }
    return {
        "delivery_channels": ["streamlit-compatibility", "fastapi", "external-integration-contract"],
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
        "integration_surfaces": [
            surface.as_dict() for surface in builtin_integration_surfaces()
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
        "scenario_contracts": [
            {
                "descriptor": {
                    "display_name": pack.descriptor.display_name,
                    "description": pack.descriptor.description,
                    "capabilities": pack.descriptor.capabilities,
                },
                "manifest": {
                    "scenario_id": pack.manifest().scenario_id,
                    "version": pack.manifest().version,
                    "research_core_version": pack.manifest().research_core_version,
                    "deprecated": pack.manifest().deprecated,
                    "replaces": pack.manifest().replaces,
                },
                "required_inputs": pack.required_inputs(),
                "workflow": [
                    {
                        "node_id": node.node_id,
                        "capability": node.capability,
                        "depends_on": node.depends_on,
                        "review_gate": node.review_gate,
                        "checkpoint": node.checkpoint,
                    }
                    for node in pack.workflow()
                ],
                "interview_policy": pack.interview_policy(),
                "evidence_policy": pack.evidence_policy(),
                "review_gates": pack.review_gates(),
                "output_schema": pack.output_schema(),
                "evaluation_rubric": pack.evaluation_rubric(),
                "report_template": pack.report_template(),
                "ui_schema": pack.ui_schema(),
                "feedback_policy": pack.feedback_policy(),
                "decision_output_policy": pack.decision_output_policy(),
                "research_route_policy": pack.research_route_policy(),
                "data_scope_policy": pack.data_scope_policy(),
            }
            for descriptor in SCENARIO_PACKS.descriptors()
            for pack in [
                SCENARIO_PACKS.get(descriptor.extension_id, descriptor.version)
            ]
        ],
    }


@app.post("/v1/projects", response_model=ProjectState, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, research: ResearchApp) -> ProjectState:
    try:
        SCENARIO_WORKFLOW.plan(
            payload.scenario_pack,
            payload.scenario_pack_version,
            payload.model_dump(),
        )
    except (KeyError, ScenarioContractError, ScenarioInputError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
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


@app.post("/v1/projects/{project_id}/interview/start", response_model=ProjectState)
def start_interview(
    project_id: str,
    payload: InterviewStartRequest,
    research: ResearchApp,
) -> ProjectState:
    try:
        project = research.get_project(project_id)
        return research.save_project(
            SCENARIO_INTERVIEWS.start(project, restart=payload.restart)
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (KeyError, ScenarioInterviewError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/interview/answer", response_model=ProjectState)
def answer_interview(
    project_id: str,
    payload: InterviewAnswerRequest,
    research: ResearchApp,
) -> ProjectState:
    try:
        project = research.get_project(project_id)
        return research.save_project(SCENARIO_INTERVIEWS.answer(project, payload.answer))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (KeyError, ScenarioInterviewError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/interview/profile", response_model=ProjectState)
def review_interview_profile(
    project_id: str, payload: ProfileReviewRequest, research: ResearchApp
) -> ProjectState:
    try:
        project = research.get_project(project_id)
        return research.save_project(SCENARIO_INTERVIEWS.review_profile(
            project,
            operating_portrait=payload.operating_portrait,
            decision_style=payload.decision_style,
            research_next_step=payload.research_next_step,
            confirm=payload.confirm,
        ))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ScenarioInterviewError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/research-route", response_model=ProjectState)
def choose_scenario_research_route(
    project_id: str,
    payload: ResearchRouteRequest,
    research: ResearchApp,
) -> ProjectState:
    try:
        project = research.get_project(project_id)
        pack = SCENARIO_PACKS.get(project.scenario_pack, project.scenario_pack_version)
        needs_interview = any(node.capability == "consulting.interview" for node in pack.workflow())
        if needs_interview and not (
            project.entity_profile_artifact and project.entity_profile_artifact.human_confirmed
        ):
            raise ScenarioInterviewError("请先完成并确认AI诊断画像，再进入专业研究")
        return research.save_project(SCENARIO_ROUTER.route(
            project,
            available_materials=payload.available_materials,
            has_existing_report=payload.has_existing_report,
        ))
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (KeyError, ScenarioInterviewError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SOPComplianceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/research-brief", response_model=ProjectState)
def review_research_brief(
    project_id: str, payload: ResearchBriefReview, research: ResearchApp
) -> ProjectState:
    try:
        return research.review_brief(
            project_id,
            changes=payload.model_dump(exclude={"confirm"}),
            confirm=payload.confirm,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/research-plan", response_model=ProjectState)
def generate_research_plan(project_id: str, research: ResearchApp) -> ProjectState:
    try:
        return research.generate_plan(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SOPComplianceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/research-plan", response_model=ProjectState)
def confirm_research_plan(
    project_id: str, payload: PlanConfirmation, research: ResearchApp
) -> ProjectState:
    try:
        if not payload.confirm:
            raise ResearchWorkflowError("Research Plan尚未确认")
        return research.confirm_plan(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/evidence", response_model=ProjectState)
async def collect_project_evidence(
    project_id: str, payload: EvidenceCollectionRequest, research: ResearchApp
) -> ProjectState:
    try:
        return await research.collect_evidence(
            project_id,
            task_ids=payload.task_ids,
            query_override=payload.query_override,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EvidenceCollectionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/evidence", response_model=ProjectState)
def review_project_evidence(
    project_id: str, payload: EvidenceReviewRequest, research: ResearchApp
) -> ProjectState:
    try:
        return research.review_evidence(
            project_id,
            decisions=[
                (item.evidence_id, item.status, item.note)
                for item in payload.decisions
            ],
            confirm=payload.confirm,
            coverage_gap_resolution=payload.coverage_gap_resolution,
            coverage_gap_user_input=payload.coverage_gap_user_input,
            coverage_gaps_acknowledged=payload.coverage_gaps_acknowledged,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (ResearchWorkflowError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/industry-analysis", response_model=ProjectState)
def generate_project_industry_analysis(
    project_id: str, research: ResearchApp
) -> ProjectState:
    try:
        return research.generate_industry_analysis(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except IndustryAnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/industry-analysis", response_model=ProjectState)
def review_project_industry_analysis(
    project_id: str, payload: IndustryAnalysisReviewRequest, research: ResearchApp
) -> ProjectState:
    try:
        return research.review_industry_analysis(
            project_id,
            decisions=[
                (item.finding_id, item.status, item.note) for item in payload.decisions
            ],
            confirm=payload.confirm,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (ResearchWorkflowError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/future-intelligence", response_model=ProjectState)
def generate_project_future_intelligence(
    project_id: str, research: ResearchApp
) -> ProjectState:
    try:
        return research.generate_future_intelligence(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except FutureIntelligenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/future-intelligence", response_model=ProjectState)
def review_project_future_intelligence(
    project_id: str, payload: FutureIntelligenceReviewRequest, research: ResearchApp
) -> ProjectState:
    try:
        return research.review_future_intelligence(
            project_id,
            decisions=[(item.item_id, item.status, item.note) for item in payload.decisions],
            confirm=payload.confirm,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (ResearchWorkflowError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/general-report", response_model=ProjectState)
def generate_project_general_report(
    project_id: str, research: ResearchApp
) -> ProjectState:
    try:
        return research.generate_general_report(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ReportGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/company-scorecard", response_model=ProjectState)
def generate_project_company_scorecard(project_id: str, research: ResearchApp) -> ProjectState:
    try:
        return research.generate_company_scorecard(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CompanyAssessmentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/company-scorecard", response_model=ProjectState)
def review_project_company_scorecard(
    project_id: str, payload: StrategyReviewRequest, research: ResearchApp
) -> ProjectState:
    try:
        return research.review_company_scorecard(
            project_id,
            decisions=[(item.item_id, item.status, item.note) for item in payload.decisions],
            confirm=payload.confirm,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (ResearchWorkflowError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/action-plan", response_model=ProjectState)
def generate_project_action_plan(project_id: str, research: ResearchApp) -> ProjectState:
    try:
        return research.generate_action_plan(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ActionPlanningError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="AI研究服务尚未完成配置") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/v1/projects/{project_id}/action-feedback", response_model=ProjectState)
def submit_project_action_feedback(
    project_id: str, payload: ActionFeedbackRequest, research: ResearchApp
) -> ProjectState:
    try:
        return research.submit_action_feedback(
            project_id,
            action_id=payload.action_id,
            progress_pct=payload.progress_pct,
            outcome_metrics=payload.outcome_metrics,
            blockers=payload.blockers,
            evidence_refs=payload.evidence_refs,
            scenario_fields=payload.scenario_fields,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except ResearchWorkflowError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.patch("/v1/projects/{project_id}/action-plan", response_model=ProjectState)
def review_project_action_plan(
    project_id: str, payload: StrategyReviewRequest, research: ResearchApp
) -> ProjectState:
    try:
        return research.review_action_plan(
            project_id,
            decisions=[(item.item_id, item.status, item.note) for item in payload.decisions],
            confirm=payload.confirm,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    except (ResearchWorkflowError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post(
    "/v1/projects/{project_id}/rewind",
    response_model=WorkflowRewindResponse,
)
def rewind_project_workflow(
    project_id: str, research: ResearchApp
) -> WorkflowRewindResponse:
    """Return to the most recent human gate and invalidate only stale outputs."""

    try:
        project = research.get_project(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="project not found") from exc
    result = rewind_to_previous_review_gate(project)
    if result is None:
        raise HTTPException(status_code=409, detail="当前没有可返回的上一审核节点")
    rewound, message = result
    return WorkflowRewindResponse(project=research.save_project(rewound), message=message)


@app.post("/v1/projects/{project_id}/report-first", response_model=ProjectState)
async def run_report_first(
    project_id: str,
    payload: PipelineRequest,
    background_tasks: BackgroundTasks,
    research: ResearchApp,
) -> ProjectState:
    if payload.background:
        try:
            queued = research.queue_report_first(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc
        except ResearchWorkflowError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        background_tasks.add_task(
            _execute_report_first_background,
            research,
            project_id,
            payload.enterprise,
        )
        return queued
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


async def _execute_report_first_background(
    research: ResearchApplication,
    project_id: str,
    enterprise: bool | None,
) -> None:
    try:
        await research.run_report_first(project_id, enterprise=enterprise)
    except ReviewerPipelineError as exc:
        research.projects.save(exc.project.model_copy(update={
            "last_pipeline_error": f"{exc.stage}：{exc}",
            "updated_at": datetime.now(UTC),
        }))
    except Exception as exc:
        # Store only the exception type; provider wrappers already expose safe
        # diagnostics and credentials must never enter project state.
        project = research.get_project(project_id)
        research.projects.save(project.model_copy(update={
            "last_pipeline_error": f"report_first：{type(exc).__name__}",
            "updated_at": datetime.now(UTC),
        }))
