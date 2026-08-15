"""Storage contract kept independent from SQLite or a future cloud database."""

from __future__ import annotations

from typing import Protocol

from src.state.project import ProjectState


class ProjectRepository(Protocol):
    def save(self, project: ProjectState) -> ProjectState: ...

    def get(self, project_id: str) -> ProjectState | None: ...

    def list(self, *, limit: int = 100, offset: int = 0) -> list[ProjectState]: ...

    def delete(self, project_id: str) -> bool: ...
