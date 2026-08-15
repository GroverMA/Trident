"""Application use cases independent of delivery channel."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from src.core.container import ServiceContainer
from src.persistence.projects import ProjectRepository
from src.state.project import ProjectState


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
