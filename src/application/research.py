"""Application use cases independent of delivery channel."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable, Mapping

from src.core.container import ServiceContainer
from src.models.research import MarketDefinition, ResearchBriefArtifact
from src.persistence.projects import ProjectRepository
from src.state.project import ProjectState, WorkflowStatus, default_workflow


class ProjectNotFoundError(LookupError):
    pass


class ResearchWorkflowError(ValueError):
    """Raised when a research command is used before its prerequisite."""


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
        if project.market_scope_confirmed_at is None:
            raise ResearchWorkflowError("请先确认研究目标与市场范围")
        brief = self.services.research_planning.generate_brief(project)
        statuses = dict(project.workflow_status)
        statuses["research_brief"] = WorkflowStatus.NEEDS_REVIEW
        statuses["research_planning"] = WorkflowStatus.NOT_STARTED
        return self.projects.save(
            project.model_copy(
                update={
                    "research_brief_artifact": brief,
                    "research_plan_artifact": None,
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
        plan = self.services.research_planning.generate_plan(project, brief)
        statuses = dict(project.workflow_status)
        statuses["research_planning"] = WorkflowStatus.NEEDS_REVIEW
        return self.projects.save(
            project.model_copy(
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

    async def run_report_first(
        self, project_id: str, *, enterprise: bool | None = None
    ) -> ProjectState:
        project = self.get_project(project_id)
        result = await self.services.reviewer_orchestration.run(
            project, enterprise=enterprise
        )
        return self.projects.save(result.project)
