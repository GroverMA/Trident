from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.app import app, build_application, get_research_application
from src.application.research import ResearchApplication
from src.persistence.sqlite_projects import SQLiteProjectRepository


def test_health_does_not_require_ai_credentials() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_uses_local_persistence_without_cloud_credentials(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("TRIDENT_ENV", "development")
    monkeypatch.setenv("TRIDENT_DATABASE_PATH", str(tmp_path / "ready.db"))
    build_application.cache_clear()

    try:
        with TestClient(app) as client:
            response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    finally:
        build_application.cache_clear()


@pytest.mark.parametrize("research_path", ["research_build_first", "report_review_first"])
def test_project_crud_is_available_without_loading_ai_runtime(
    tmp_path, research_path: str
) -> None:
    def fail_if_ai_runtime_is_loaded():
        raise AssertionError("AI runtime should be lazy for project CRUD")

    research = ResearchApplication(
        projects=SQLiteProjectRepository(tmp_path / "api.db"),
        service_factory=fail_if_ai_runtime_is_loaded,
    )
    app.dependency_overrides[get_research_application] = lambda: research
    payload = {
        "project_name": "全球及中国IVD市场研究",
        "industry": "IVD",
        "region": "全球及中国",
        "research_objective": "研究市场现状、未来十年发展和竞争格局",
        "time_horizon": "2026-2036",
        "research_path": research_path,
    }

    try:
        with TestClient(app) as client:
            created = client.post("/v1/projects", json=payload)
            assert created.status_code == 201
            project = created.json()

            listed = client.get("/v1/projects")
            assert listed.status_code == 200
            assert listed.json()[0]["project_id"] == project["project_id"]

            fetched = client.get(f"/v1/projects/{project['project_id']}")
            assert fetched.status_code == 200
            assert fetched.json()["project_name"] == payload["project_name"]
            assert fetched.json()["research_path"] == research_path

            scope = client.patch(
                f"/v1/projects/{project['project_id']}/scope",
                json={
                    "project_name": payload["project_name"],
                    "industry": payload["industry"],
                    "region": payload["region"],
                    "research_objective": payload["research_objective"]
                    + "，重点验证主要玩家的竞争位置",
                    "time_horizon": payload["time_horizon"],
                    "output_language": "简体中文",
                    "confirm": True,
                },
            )
            assert scope.status_code == 200
            confirmed = scope.json()
            assert confirmed["current_step"] == "research_planning"
            assert confirmed["market_scope_confirmed_at"] is not None
            assert confirmed["workflow_status"]["research_brief"] == "completed"
            assert confirmed["workflow_status"]["research_planning"] == "ready"

            persisted = client.get(f"/v1/projects/{project['project_id']}").json()
            assert persisted["research_objective"].endswith("主要玩家的竞争位置")
            assert persisted["market_scope_confirmed_at"] is not None

            deleted = client.delete(f"/v1/projects/{project['project_id']}")
            assert deleted.status_code == 204
            assert client.get(f"/v1/projects/{project['project_id']}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_scope_update_rejects_empty_required_fields(tmp_path) -> None:
    research = ResearchApplication(
        projects=SQLiteProjectRepository(tmp_path / "api.db"),
        service_factory=lambda: (_ for _ in ()).throw(
            AssertionError("AI runtime should not load")
        ),
    )
    app.dependency_overrides[get_research_application] = lambda: research
    try:
        with TestClient(app) as client:
            project = client.post(
                "/v1/projects",
                json={
                    "project_name": "IVD研究",
                    "industry": "IVD",
                    "region": "中国",
                    "research_objective": "研究竞争格局",
                    "time_horizon": "2026-2036",
                },
            ).json()
            response = client.patch(
                f"/v1/projects/{project['project_id']}/scope",
                json={
                    "project_name": "IVD研究",
                    "industry": "",
                    "region": "中国",
                    "research_objective": "研究竞争格局",
                    "time_horizon": "2026-2036",
                    "confirm": True,
                },
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
