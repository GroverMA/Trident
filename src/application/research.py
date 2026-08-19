"""Application use cases independent of delivery channel."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable, Mapping, TypeVar

from src.core.container import ServiceContainer
from src.models.evidence import EvidenceReviewStatus
from src.models.analysis import AnalysisReviewStatus
from src.models.future import ForecastReviewStatus
from src.models.research import MarketDefinition, ResearchBriefArtifact
from src.observability.telemetry import StepRunTelemetry, finish_span, start_span
from src.persistence.projects import ProjectRepository
from src.state.project import ProjectState, WorkflowStatus, default_workflow
from src.services.evidence_collection import (
    evidence_coverage_advisories,
    evidence_gate_reasons,
    review_evidence,
    upsert_task_run,
)
from src.services.industry_analysis import (
    analysis_gate_reasons,
    review_analysis_finding,
)
from src.services.future_intelligence import forecast_gate_reasons, review_forecast_item


class ProjectNotFoundError(LookupError):
    pass


class ResearchWorkflowError(ValueError):
    """Raised when a research command is used before its prerequisite."""


T = TypeVar("T")


class ResearchApplication:
    def __init__(
        self,
        *,
        projects: ProjectRepository,
        services: ServiceContainer | None = None,
        service_factory: Callable[[], ServiceContainer] = ServiceContainer.from_runtime,
    ) -> None:
        self._services = services
        self._service_factory = service_factory
        self.projects = projects

    @property
    def services(self) -> ServiceContainer:
        """Load AI runtime only when an AI-backed use case is executed."""
        if self._services is None:
            self._services = self._service_factory()
        return self._services

    def create_project(self, project: ProjectState) -> ProjectState:
        return self.projects.save(project)

    def get_project(self, project_id: str) -> ProjectState:
        project = self.projects.get(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    def save_project(self, project: ProjectState) -> ProjectState:
        if self.projects.get(project.project_id) is None:
            raise ProjectNotFoundError(project.project_id)
        updated = project.model_copy(update={"updated_at": datetime.now(UTC)})
        return self.projects.save(updated)

    def list_projects(self, *, limit: int = 100, offset: int = 0) -> list[ProjectState]:
        return self.projects.list(limit=limit, offset=offset)

    def delete_project(self, project_id: str) -> bool:
        return self.projects.delete(project_id)

    def check_persistence(self) -> None:
        self.projects.ping()

    @staticmethod
    def _append_telemetry(
        project: ProjectState, run: StepRunTelemetry
    ) -> ProjectState:
        # Project payload persistence keeps telemetry deployment-neutral for the
        # demo. Bound history prevents one long-running project growing without
        # limit; the commercial database phase will move these rows to an
        # append-only telemetry table.
        return project.model_copy(
            update={"telemetry_runs": [*project.telemetry_runs, run][-500:]}
        )

    def _run_ai_step(
        self,
        project: ProjectState,
        step: str,
        operation: Callable[[], T],
        *,
        task_id: str | None = None,
    ) -> tuple[T, StepRunTelemetry]:
        span, token = start_span(project.project_id, step, task_id)
        try:
            result = operation()
        except Exception as exc:
            run = finish_span(span, token, exc)
            latest = self.get_project(project.project_id)
            self.projects.save(self._append_telemetry(latest, run))
            raise
        return result, finish_span(span, token)

    def update_scope(
        self,
        project_id: str,
        *,
        scope: dict[str, object],
        confirm: bool,
    ) -> ProjectState:
        """Save or confirm the research scope without loading the AI runtime.

        The same project state is used by build-first and review-first.  A
        material draft edit deliberately invalidates downstream artifacts so
        an old report can never be presented against a new market boundary.
        """

        project = self.get_project(project_id)
        material_fields = {
            "project_name",
            "industry",
            "region",
            "research_objective",
            "time_horizon",
            "output_language",
            "target_company",
            "company_strategy_objective",
        }
        changed = any(
            field in scope and scope[field] != getattr(project, field)
            for field in material_fields
        )
        now = datetime.now(UTC)
        payload = project.model_dump()
        payload.update(scope)

        if changed:
            statuses = default_workflow()
            if not project.company_strategy_enabled:
                statuses["company_assessment"] = WorkflowStatus.NOT_APPLICABLE
                statuses["action_plan"] = WorkflowStatus.NOT_APPLICABLE
            payload.update(
                {
                    "research_brief_artifact": None,
                    "research_plan_artifact": None,
                    "evidence_collection_artifact": None,
                    "industry_analysis_artifact": None,
                    "future_intelligence_artifact": None,
                    "general_report_artifact": None,
                    "company_scorecard_artifact": None,
                    "action_plan_artifact": None,
                    "enterprise_decision_report_artifact": None,
                    "content_revision_artifact": None,
                    "execution_authorized_at": None,
                    "market_scope_confirmed_at": None,
                    "workflow_status": statuses,
                    "current_step": "research_brief",
                }
            )

        # Reconfirming an unchanged scope is idempotent.  In particular, it
        # must not move an in-progress project back to Research Brief or erase
        # the status of an already reviewed brief/plan.
        if confirm and (changed or project.market_scope_confirmed_at is None):
            statuses = dict(payload["workflow_status"])
            statuses["research_brief"] = WorkflowStatus.READY
            statuses["research_planning"] = WorkflowStatus.NOT_STARTED
            payload.update(
                {
                    "market_scope_confirmed_at": now,
                    "workflow_status": statuses,
                    "current_step": "research_brief",
                }
            )
        elif confirm:
            payload["market_scope_confirmed_at"] = now

        payload["updated_at"] = now
        updated = ProjectState.model_validate(payload)
        return self.projects.save(updated)

    def generate_brief(self, project_id: str) -> ProjectState:
        project = self.get_project(project_id)
        brief, telemetry = self._run_ai_step(
            project,
            "research_brief",
            lambda: self.services.research_planning.generate_brief(project),
        )
        statuses = dict(project.workflow_status)
        statuses["research_brief"] = WorkflowStatus.NEEDS_REVIEW
        statuses["research_planning"] = WorkflowStatus.NOT_STARTED
        return self.projects.save(
            self._append_telemetry(project, telemetry).model_copy(
                update={
                    "research_brief_artifact": brief,
                    "research_plan_artifact": None,
                    "market_scope_confirmed_at": None,
                    "workflow_status": statuses,
                    "current_step": "research_brief",
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def review_brief(
        self,
        project_id: str,
        *,
        changes: Mapping[str, object],
        confirm: bool,
    ) -> ProjectState:
        project = self.get_project(project_id)
        brief = project.research_brief_artifact
        if brief is None:
            raise ResearchWorkflowError("请先生成Research Brief")

        payload = brief.model_dump()
        payload.update(changes)
        if isinstance(payload.get("market_definition"), dict):
            payload["market_definition"] = MarketDefinition.model_validate(
                payload["market_definition"]
            )
        now = datetime.now(UTC)
        payload.update(
            {
                "human_confirmed": confirm,
                "confirmed_at": now if confirm else None,
            }
        )
        reviewed = ResearchBriefArtifact.model_validate(payload)
        statuses = dict(project.workflow_status)
        statuses["research_brief"] = (
            WorkflowStatus.COMPLETED if confirm else WorkflowStatus.NEEDS_REVIEW
        )
        statuses["research_planning"] = (
            WorkflowStatus.READY if confirm else WorkflowStatus.NOT_STARTED
        )
        return self.projects.save(
            project.model_copy(
                update={
                    "research_brief_artifact": reviewed,
                    "research_plan_artifact": None,
                    "market_scope_confirmed_at": now if confirm else None,
                    "workflow_status": statuses,
                    "current_step": "research_planning" if confirm else "research_brief",
                    "updated_at": now,
                }
            )
        )

    def generate_plan(self, project_id: str) -> ProjectState:
        project = self.get_project(project_id)
        brief = project.research_brief_artifact
        if brief is None or not brief.human_confirmed:
            raise ResearchWorkflowError("Research Brief必须先经过人工确认")
        plan, telemetry = self._run_ai_step(
            project,
            "research_planning",
            lambda: self.services.research_planning.generate_plan(project, brief),
        )
        statuses = dict(project.workflow_status)
        statuses["research_planning"] = WorkflowStatus.NEEDS_REVIEW
        return self.projects.save(
            self._append_telemetry(project, telemetry).model_copy(
                update={
                    "research_plan_artifact": plan,
                    "workflow_status": statuses,
                    "current_step": "research_planning",
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def confirm_plan(self, project_id: str) -> ProjectState:
        project = self.get_project(project_id)
        plan = project.research_plan_artifact
        if plan is None:
            raise ResearchWorkflowError("请先生成Research Plan")
        statuses = dict(project.workflow_status)
        statuses["research_planning"] = WorkflowStatus.COMPLETED
        statuses["evidence_collection"] = WorkflowStatus.READY
        next_step = "evidence_collection"
        if project.research_path.value == "report_review_first":
            statuses["decision_report"] = WorkflowStatus.READY
            next_step = "decision_report"
        return self.projects.save(
            project.model_copy(
                update={
                    "research_plan_artifact": plan.model_copy(
                        update={"human_confirmed": True}
                    ),
                    "workflow_status": statuses,
                    "current_step": next_step,
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    async def collect_evidence(
        self,
        project_id: str,
        *,
        task_ids: list[str] | None = None,
        query_override: str | None = None,
    ) -> ProjectState:
        """Execute one or all approved research tasks and persist Gate 1 evidence."""

        project = self.get_project(project_id)
        plan = project.research_plan_artifact
        if plan is None or not plan.human_confirmed:
            raise ResearchWorkflowError("Research Plan必须先经过人工确认")

        available = {task.task_id for task in plan.tasks}
        selected = task_ids or [task.task_id for task in plan.tasks]
        unknown = [task_id for task_id in selected if task_id not in available]
        if unknown:
            raise ResearchWorkflowError(f"研究计划中不存在任务：{', '.join(unknown)}")
        if query_override and len(selected) != 1:
            raise ResearchWorkflowError("自定义检索式只能用于单个研究任务")

        statuses = dict(project.workflow_status)
        statuses["evidence_collection"] = WorkflowStatus.IN_PROGRESS
        active = self.projects.save(
            project.model_copy(
                update={
                    "workflow_status": statuses,
                    "current_step": "evidence_collection",
                    "last_pipeline_error": None,
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        artifact = active.evidence_collection_artifact
        for task_id in selected:
            span, token = start_span(active.project_id, "evidence_collection", task_id)
            try:
                run = await self.services.evidence_collection.collect_task(
                    active,
                    plan,
                    task_id,
                    query_override=query_override,
                )
            except Exception as exc:
                telemetry = finish_span(span, token, exc)
                statuses = dict(active.workflow_status)
                statuses["evidence_collection"] = (
                    WorkflowStatus.NEEDS_REVIEW
                    if artifact is not None and artifact.task_runs
                    else WorkflowStatus.READY
                )
                self.projects.save(self._append_telemetry(active, telemetry).model_copy(update={
                    "workflow_status": statuses,
                    "current_step": "evidence_collection",
                    "last_pipeline_error": f"{task_id}：{exc}",
                    "updated_at": datetime.now(UTC),
                }))
                raise
            telemetry = finish_span(span, token)
            artifact = upsert_task_run(artifact, plan.artifact_id, run)
            active = self.projects.save(
                self._append_telemetry(active, telemetry).model_copy(
                    update={
                        "evidence_collection_artifact": artifact,
                        "updated_at": datetime.now(UTC),
                    }
                )
            )

        statuses = dict(active.workflow_status)
        statuses["evidence_collection"] = WorkflowStatus.NEEDS_REVIEW
        statuses["evidence_qa"] = WorkflowStatus.NEEDS_REVIEW
        return self.projects.save(
            active.model_copy(
                update={
                    "workflow_status": statuses,
                    "current_step": "evidence_qa",
                    "last_pipeline_error": None,
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def review_evidence(
        self,
        project_id: str,
        *,
        decisions: list[tuple[str, EvidenceReviewStatus, str | None]],
        confirm: bool,
        coverage_gap_resolution: str | None = None,
        coverage_gap_user_input: str | None = None,
        coverage_gaps_acknowledged: bool = False,
    ) -> ProjectState:
        """Persist Gate 1 decisions and open analysis only after human confirmation."""

        project = self.get_project(project_id)
        plan = project.research_plan_artifact
        artifact = project.evidence_collection_artifact
        if plan is None or artifact is None:
            raise ResearchWorkflowError("请先完成证据检索")

        reviewed = artifact
        for evidence_id, decision, note in decisions:
            reviewed = review_evidence(reviewed, evidence_id, decision, note)

        statuses = dict(project.workflow_status)
        current_step = "evidence_qa"
        if confirm:
            reasons = evidence_gate_reasons(reviewed, plan)
            if reasons:
                raise ResearchWorkflowError("；".join(reasons))
            advisories = evidence_coverage_advisories(reviewed, plan)
            if advisories:
                if not coverage_gaps_acknowledged:
                    raise ResearchWorkflowError("请先确认已阅读证据缺口及处理方式")
                if coverage_gap_resolution not in {
                    "accept_analyst_handling",
                    "user_input",
                }:
                    raise ResearchWorkflowError("请选择证据缺口处理方式")
                if (
                    coverage_gap_resolution == "user_input"
                    and not (coverage_gap_user_input or "").strip()
                ):
                    raise ResearchWorkflowError("请补充你的行业判断或采用口径")
            reviewed = reviewed.model_copy(
                update={
                    "human_confirmed": True,
                    "coverage_gap_resolution": coverage_gap_resolution,
                    "coverage_gap_user_input": (
                        (coverage_gap_user_input or "").strip() or None
                    ),
                    "coverage_gaps_acknowledged_at": (
                        datetime.now(UTC) if advisories else None
                    ),
                }
            )
            statuses["evidence_collection"] = WorkflowStatus.COMPLETED
            statuses["evidence_qa"] = WorkflowStatus.COMPLETED
            statuses["industry_analysis"] = WorkflowStatus.READY
            current_step = "industry_analysis"
        else:
            statuses["evidence_collection"] = WorkflowStatus.NEEDS_REVIEW
            statuses["evidence_qa"] = WorkflowStatus.NEEDS_REVIEW

        return self.projects.save(
            project.model_copy(
                update={
                    "evidence_collection_artifact": reviewed,
                    "workflow_status": statuses,
                    "current_step": current_step,
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def generate_industry_analysis(self, project_id: str) -> ProjectState:
        """Generate the five evidence-grounded current-industry modules."""

        project = self.get_project(project_id)
        evidence = project.evidence_collection_artifact
        if evidence is None or not evidence.human_confirmed:
            raise ResearchWorkflowError("Gate 1证据必须先经过人工确认")
        analysis, telemetry = self._run_ai_step(
            project,
            "industry_analysis",
            lambda: self.services.industry_analysis.generate(project, evidence),
        )
        statuses = dict(project.workflow_status)
        statuses["industry_analysis"] = WorkflowStatus.NEEDS_REVIEW
        statuses["future_intelligence"] = WorkflowStatus.NOT_STARTED
        return self.projects.save(
            self._append_telemetry(project, telemetry).model_copy(
                update={
                    "industry_analysis_artifact": analysis,
                    "future_intelligence_artifact": None,
                    "general_report_artifact": None,
                    "workflow_status": statuses,
                    "current_step": "industry_analysis",
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def review_industry_analysis(
        self,
        project_id: str,
        *,
        decisions: list[tuple[str, AnalysisReviewStatus, str | None]],
        confirm: bool,
    ) -> ProjectState:
        """Persist finding decisions and open Future Intelligence at the gate."""

        project = self.get_project(project_id)
        analysis = project.industry_analysis_artifact
        evidence = project.evidence_collection_artifact
        if analysis is None or evidence is None:
            raise ResearchWorkflowError("请先生成行业分析")
        if analysis.evidence_collection_id != evidence.artifact_id:
            raise ResearchWorkflowError("Evidence Matrix已经变化，请重新生成行业分析")

        reviewed = analysis
        for finding_id, decision, note in decisions:
            reviewed = review_analysis_finding(reviewed, finding_id, decision, note)

        statuses = dict(project.workflow_status)
        current_step = "industry_analysis"
        if confirm:
            reasons = analysis_gate_reasons(reviewed)
            if reasons:
                raise ResearchWorkflowError("；".join(reasons))
            reviewed = reviewed.model_copy(
                update={"human_confirmed": True, "updated_at": datetime.now(UTC)}
            )
            statuses["industry_analysis"] = WorkflowStatus.COMPLETED
            statuses["future_intelligence"] = WorkflowStatus.READY
            current_step = "future_intelligence"
        else:
            statuses["industry_analysis"] = WorkflowStatus.NEEDS_REVIEW

        return self.projects.save(
            project.model_copy(
                update={
                    "industry_analysis_artifact": reviewed,
                    "future_intelligence_artifact": None,
                    "general_report_artifact": None,
                    "workflow_status": statuses,
                    "current_step": current_step,
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def generate_future_intelligence(self, project_id: str) -> ProjectState:
        """Generate evidence-linked trends and scenarios after Industry Analysis."""

        project = self.get_project(project_id)
        evidence = project.evidence_collection_artifact
        analysis = project.industry_analysis_artifact
        if evidence is None or analysis is None or not analysis.human_confirmed:
            raise ResearchWorkflowError("请先完成人工确认的行业分析")
        future, telemetry = self._run_ai_step(
            project,
            "future_intelligence",
            lambda: self.services.future_intelligence.generate(project, evidence, analysis),
        )
        statuses = dict(project.workflow_status)
        statuses["future_intelligence"] = WorkflowStatus.NEEDS_REVIEW
        statuses["human_review"] = WorkflowStatus.NOT_STARTED
        statuses["decision_report"] = WorkflowStatus.NOT_STARTED
        return self.projects.save(self._append_telemetry(project, telemetry).model_copy(update={
            "future_intelligence_artifact": future,
            "general_report_artifact": None,
            "workflow_status": statuses,
            "current_step": "future_intelligence",
            "updated_at": datetime.now(UTC),
        }))

    def review_future_intelligence(
        self,
        project_id: str,
        *,
        decisions: list[tuple[str, ForecastReviewStatus, str | None]],
        confirm: bool,
    ) -> ProjectState:
        """Persist trend/scenario decisions and open Gate 2 or strategy work."""

        project = self.get_project(project_id)
        future = project.future_intelligence_artifact
        analysis = project.industry_analysis_artifact
        evidence = project.evidence_collection_artifact
        if future is None or analysis is None or evidence is None:
            raise ResearchWorkflowError("请先生成Future Intelligence")
        if (
            future.industry_analysis_id != analysis.artifact_id
            or future.evidence_collection_id != evidence.artifact_id
        ):
            raise ResearchWorkflowError("上游研究产物已经变化，请重新生成Future Intelligence")

        reviewed = future
        for item_id, decision, note in decisions:
            reviewed = review_forecast_item(reviewed, item_id, decision, note)

        statuses = dict(project.workflow_status)
        current_step = "future_intelligence"
        if confirm:
            # Streamlit parity: Gate 2 defaults every non-rejected item to
            # included. Reviewers only need to act when they want to exclude
            # content; untouched items must never create an accidental block.
            for item in [*reviewed.trends, *reviewed.scenarios]:
                if item.review_status == ForecastReviewStatus.NEEDS_REVIEW:
                    item_id = getattr(item, "trend_id", None) or getattr(item, "scenario_id")
                    reviewed = review_forecast_item(
                        reviewed,
                        item_id,
                        ForecastReviewStatus.ACCEPTED,
                        "Gate 2默认采用；用户未明确排除",
                    )
            reasons = forecast_gate_reasons(reviewed)
            if reasons:
                raise ResearchWorkflowError("；".join(reasons))
            reviewed = reviewed.model_copy(update={
                "human_confirmed": True,
                "updated_at": datetime.now(UTC),
            })
            statuses["future_intelligence"] = WorkflowStatus.COMPLETED
            if project.company_strategy_enabled:
                statuses["company_assessment"] = WorkflowStatus.READY
                current_step = "company_assessment"
            else:
                statuses["company_assessment"] = WorkflowStatus.NOT_APPLICABLE
                statuses["action_plan"] = WorkflowStatus.NOT_APPLICABLE
                statuses["human_review"] = WorkflowStatus.READY
                current_step = "human_review"
        else:
            statuses["future_intelligence"] = WorkflowStatus.NEEDS_REVIEW

        return self.projects.save(project.model_copy(update={
            "future_intelligence_artifact": reviewed,
            "general_report_artifact": None,
            "workflow_status": statuses,
            "current_step": current_step,
            "updated_at": datetime.now(UTC),
        }))

    def generate_general_report(self, project_id: str) -> ProjectState:
        """Complete Gate 2 and compose a report from approved content only."""

        project = self.get_project(project_id)
        analysis = project.industry_analysis_artifact
        future = project.future_intelligence_artifact
        if analysis is None or not analysis.human_confirmed:
            raise ResearchWorkflowError("行业分析尚未通过人工审核")
        if future is None or not future.human_confirmed:
            raise ResearchWorkflowError("Future Intelligence尚未通过人工审核")
        report, telemetry = self._run_ai_step(
            project,
            "decision_report",
            lambda: self.services.report_generation.generate(project),
        )
        statuses = dict(project.workflow_status)
        statuses["human_review"] = WorkflowStatus.COMPLETED
        statuses["decision_report"] = WorkflowStatus.COMPLETED
        return self.projects.save(self._append_telemetry(project, telemetry).model_copy(update={
            "general_report_artifact": report,
            "workflow_status": statuses,
            "current_step": "decision_report",
            "updated_at": datetime.now(UTC),
        }))

    async def run_report_first(
        self, project_id: str, *, enterprise: bool | None = None
    ) -> ProjectState:
        project = self.get_project(project_id)
        result = await self.services.reviewer_orchestration.run(
            project, enterprise=enterprise
        )
        return self.projects.save(result.project)

    def queue_report_first(self, project_id: str) -> ProjectState:
        """Persist a visible queued state before background report execution."""

        project = self.get_project(project_id)
        brief = project.research_brief_artifact
        plan = project.research_plan_artifact
        if brief is None or not brief.human_confirmed:
            raise ResearchWorkflowError("Research Brief必须先经过人工确认")
        if plan is None or not plan.human_confirmed:
            raise ResearchWorkflowError("Research Plan必须先经过人工确认")
        if project.workflow_status.get("decision_report") == WorkflowStatus.IN_PROGRESS:
            raise ResearchWorkflowError("报告初稿已经在后台生成，请等待当前任务完成")
        statuses = dict(project.workflow_status)
        statuses["decision_report"] = WorkflowStatus.IN_PROGRESS
        return self.projects.save(project.model_copy(update={
            "workflow_status": statuses,
            "current_step": "decision_report",
            "last_pipeline_error": None,
            "updated_at": datetime.now(UTC),
        }))
