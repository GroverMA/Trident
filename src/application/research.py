"""Application use cases independent of delivery channel."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from src.core.container import ServiceContainer
from src.persistence.projects import ProjectRepository
from src.state.project import ProjectState, WorkflowStatus, default_workflow


class ProjectNotFoundError(LookupError):
    pass


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

        if confirm:
            statuses = dict(payload["workflow_status"])
            statuses["research_brief"] = WorkflowStatus.COMPLETED
            statuses["research_planning"] = WorkflowStatus.READY
            payload.update(
                {
                    "market_scope_confirmed_at": now,
                    "workflow_status": statuses,
                    "current_step": "research_planning",
                }
            )

        payload["updated_at"] = now
        updated = ProjectState.model_validate(payload)
        return self.projects.save(updated)

    def generate_brief(self, project_id: str) -> ProjectState:
        project = self.get_project(project_id)
        brief = self.services.research_planning.generate_brief(project)
        return self.projects.save(
            project.model_copy(
                update={
                    "research_brief_artifact": brief,
                    "current_step": "research_brief",
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
