from __future__ import annotations

import pytest

from src.persistence.factory import (
    PersistenceConfigurationError,
    create_project_repository,
)
from src.persistence.postgres_projects import PostgresProjectRepository
from src.persistence.sqlite_projects import SQLiteProjectRepository
from src.state.project import ProjectState


def make_project(name: str = "中国IVD研究") -> ProjectState:
    return ProjectState(
        project_name=name,
        industry="IVD",
        region="中国",
        research_objective="研究市场现状、竞争格局与未来趋势",
        time_horizon="2026-2036",
    )


def test_sqlite_repository_round_trip_and_delete(tmp_path) -> None:
    repository = SQLiteProjectRepository(tmp_path / "projects.db")
    project = make_project()

    repository.save(project)
    restored = repository.get(project.project_id)

    assert restored == project
    assert repository.list() == [project]
    assert repository.delete(project.project_id) is True
    assert repository.get(project.project_id) is None
    assert repository.delete(project.project_id) is False


def test_sqlite_repository_updates_payload_and_orders_by_update_time(tmp_path) -> None:
    repository = SQLiteProjectRepository(tmp_path / "projects.db")
    first = make_project("项目一")
    second = make_project("项目二").model_copy(
        update={"updated_at": first.updated_at.replace(year=first.updated_at.year + 1)}
    )
    repository.save(first)
    repository.save(second)

    updated = first.model_copy(update={"current_step": "evidence_collection"})
    repository.save(updated)

    assert repository.get(first.project_id).current_step == "evidence_collection"
    assert repository.list(limit=1)[0].project_id == second.project_id


def test_production_repository_requires_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TRIDENT_ALLOW_SQLITE", raising=False)

    with pytest.raises(PersistenceConfigurationError, match="DATABASE_URL is required"):
        create_project_repository()


def test_sqlite_requires_explicit_local_opt_in(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("TRIDENT_ALLOW_SQLITE", "true")
    monkeypatch.setenv("TRIDENT_DATABASE_PATH", str(tmp_path / "local.db"))

    assert isinstance(create_project_repository(), SQLiteProjectRepository)


def test_postgres_adapter_rejects_non_postgres_urls() -> None:
    with pytest.raises(ValueError, match="requires a PostgreSQL URL"):
        PostgresProjectRepository("sqlite:///unsafe.db")
