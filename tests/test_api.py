from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from src.api.app import app, build_application, get_research_application
from src.application.research import ResearchApplication
from src.persistence.sqlite_projects import SQLiteProjectRepository
from src.state.project import ProjectState, WorkflowStatus
from src.models.research import (
    MarketDefinition,
    MethodologyTrace,
    ResearchBriefArtifact,
    ResearchPlanArtifact,
    ResearchTask,
)
from src.models.evidence import EvidenceItem, EvidenceKind, TaskEvidenceRun


def methodology() -> MethodologyTrace:
    return MethodologyTrace(
        sop_id="trident-sop",
        sop_name="Trident行业研究方法",
        sop_version="3.0",
        sop_hash="test-hash",
        rule_ids=["R01", "R02"],
    )


class FakeResearchPlanningService:
    def generate_brief(self, project):
        return ResearchBriefArtifact(
            decision_statement="明确全球及中国IVD市场的增长与竞争判断",
            original_prompt=project.research_objective,
            market_definition=MarketDefinition(
                core_market="体外诊断市场",
                product_scope="试剂、仪器、耗材与配套软件",
                customer_scope="医疗机构、第三方实验室和公共卫生机构",
                geography_scope=project.region,
                value_chain_scope="上游原材料至终端应用",
                time_scope=project.time_horizon,
                inclusions=["免疫诊断", "分子诊断", "POCT"],
                exclusions=["治疗性药物", "医学影像设备"],
            ),
            key_questions=["市场规模与增长如何？", "主要竞争者如何布局？"],
            information_gaps=["细分赛道口径仍需验证"],
            hypotheses=["基层诊疗和国产替代将驱动增长"],
            clarification_questions=["是否包含港澳市场？"],
            confidence_note="范围可用于启动研究，关键口径需人工确认。",
            methodology=methodology(),
        )

    def generate_plan(self, project, brief):
        return ResearchPlanArtifact(
            plan_summary="围绕市场、竞争和未来趋势形成可追溯研究底稿。",
            tasks=[
                ResearchTask(
                    task_id="T01",
                    title="市场定义与规模",
                    objective="统一市场边界并测算规模",
                    questions=["市场包含哪些细分赛道？"],
                    hypotheses=["市场保持结构性增长"],
                    information_needs=["市场规模", "细分结构"],
                    preferred_sources=["监管机构", "公司披露"],
                    search_queries=["全球 中国 IVD 市场规模 2026"],
                    deliverables=["市场定义", "规模测算"],
                    evidence_standard="至少两类独立来源相互校验",
                    validation_gate="人工确认口径与证据可用性",
                    prompt_question_ids=["Q01"],
                )
            ],
            human_review_gates=["市场口径确认", "证据可用性确认"],
            unresolved_gaps=["港澳市场是否纳入"],
            sop_coverage={"industry_definition": ["T01"]},
            prompt_question_coverage={"Q01": ["T01"]},
            methodology=methodology(),
        )


class FakeEvidenceCollectionService:
    async def collect_task(self, project, plan, task_id, *, query_override=None):
        return TaskEvidenceRun(
            task_id=task_id,
            task_title=plan.tasks[0].title,
            queries_used=[query_override or plan.tasks[0].search_queries[0]],
            evidence=[
                EvidenceItem(
                    task_id=task_id,
                    source_id="SRC-api-test",
                    kind=EvidenceKind.DATA,
                    statement="官方披露显示该市场保持结构性增长。",
                    supporting_excerpt="该市场保持结构性增长",
                    geographic_scope=project.region,
                    market_scope=project.industry,
                    supports_or_challenges="supports",
                    model_confidence=0.9,
                    prompt_relevance=0.95,
                    qa_score=92,
                )
            ],
        )

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
            assert confirmed["current_step"] == "research_brief"
            assert confirmed["market_scope_confirmed_at"] is not None
            assert confirmed["workflow_status"]["research_brief"] == "ready"
            assert confirmed["workflow_status"]["research_planning"] == "not_started"

            persisted = client.get(f"/v1/projects/{project['project_id']}").json()
            assert persisted["research_objective"].endswith("主要玩家的竞争位置")
            assert persisted["market_scope_confirmed_at"] is not None

            deleted = client.delete(f"/v1/projects/{project['project_id']}")
            assert deleted.status_code == 204
            assert client.get(f"/v1/projects/{project['project_id']}").status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("research_path", ["research_build_first", "report_review_first"])
def test_research_brief_and_plan_workflow_persists_for_both_paths(
    tmp_path, research_path: str
) -> None:
    services = SimpleNamespace(research_planning=FakeResearchPlanningService())
    research = ResearchApplication(
        projects=SQLiteProjectRepository(tmp_path / f"{research_path}.db"),
        services=services,
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
            project = client.post("/v1/projects", json=payload).json()
            project_url = f"/v1/projects/{project['project_id']}"

            blocked = client.post(f"{project_url}/research-brief")
            assert blocked.status_code == 409

            scope_payload = {
                **{key: payload[key] for key in (
                    "project_name", "industry", "region", "research_objective", "time_horizon"
                )},
                "output_language": "简体中文",
                "confirm": True,
            }
            assert client.patch(f"{project_url}/scope", json=scope_payload).status_code == 200

            generated = client.post(f"{project_url}/research-brief")
            assert generated.status_code == 200
            brief = generated.json()["research_brief_artifact"]
            assert brief["human_confirmed"] is False
            assert generated.json()["workflow_status"]["research_brief"] == "needs_review"

            review_payload = {
                "decision_statement": brief["decision_statement"],
                "market_definition": brief["market_definition"],
                "key_questions": brief["key_questions"],
                "information_gaps": brief["information_gaps"],
                "hypotheses": brief["hypotheses"],
                "clarification_questions": brief["clarification_questions"],
                "clarification_responses": {"是否包含港澳市场？": "包含"},
                "confidence_note": brief["confidence_note"],
                "confirm": True,
            }
            reviewed = client.patch(f"{project_url}/research-brief", json=review_payload)
            assert reviewed.status_code == 200
            assert reviewed.json()["research_brief_artifact"]["human_confirmed"] is True
            assert reviewed.json()["workflow_status"]["research_planning"] == "ready"

            planned = client.post(f"{project_url}/research-plan")
            assert planned.status_code == 200
            assert planned.json()["research_plan_artifact"]["tasks"][0]["task_id"] == "T01"
            assert planned.json()["workflow_status"]["research_planning"] == "needs_review"

            confirmed = client.patch(
                f"{project_url}/research-plan", json={"confirm": True}
            )
            assert confirmed.status_code == 200
            body = confirmed.json()
            assert body["research_plan_artifact"]["human_confirmed"] is True
            assert body["workflow_status"]["research_planning"] == "completed"
            assert body["workflow_status"]["evidence_collection"] == "ready"
            expected_step = (
                "decision_report" if research_path == "report_review_first" else "evidence_collection"
            )
            assert body["current_step"] == expected_step

            persisted = client.get(project_url).json()
            assert persisted["research_brief_artifact"]["human_confirmed"] is True
            assert persisted["research_plan_artifact"]["human_confirmed"] is True

            # Reopening and reconfirming an unchanged scope must preserve all
            # downstream work and the current workflow position.
            reconfirmed = client.patch(f"{project_url}/scope", json=scope_payload)
            assert reconfirmed.status_code == 200
            reconfirmed_body = reconfirmed.json()
            assert reconfirmed_body["current_step"] == expected_step
            assert reconfirmed_body["research_brief_artifact"]["human_confirmed"] is True
            assert reconfirmed_body["research_plan_artifact"]["human_confirmed"] is True
            assert reconfirmed_body["workflow_status"]["research_planning"] == "completed"
    finally:
        app.dependency_overrides.clear()


def test_build_first_evidence_gate_is_service_backed_and_persisted(tmp_path) -> None:
    repository = SQLiteProjectRepository(tmp_path / "evidence-api.db")
    research_plan = FakeResearchPlanningService().generate_plan(
        ProjectState(
            project_name="IVD研究",
            industry="IVD",
            region="中国",
            research_objective="研究竞争格局",
            time_horizon="2026-2036",
        ),
        None,
    ).model_copy(update={"human_confirmed": True})
    statuses = {
        key: WorkflowStatus.NOT_STARTED
        for key in ProjectState(
            project_name="占位",
            industry="IVD",
            region="中国",
            research_objective="研究",
            time_horizon="2026-2036",
        ).workflow_status
    }
    statuses["research_planning"] = WorkflowStatus.COMPLETED
    statuses["evidence_collection"] = WorkflowStatus.READY
    project = repository.save(
        ProjectState(
            project_name="IVD研究",
            industry="IVD",
            region="中国",
            research_objective="研究竞争格局",
            time_horizon="2026-2036",
            research_plan_artifact=research_plan,
            workflow_status=statuses,
            current_step="evidence_collection",
        )
    )
    services = SimpleNamespace(
        evidence_collection=FakeEvidenceCollectionService(),
    )
    research = ResearchApplication(projects=repository, services=services)
    app.dependency_overrides[get_research_application] = lambda: research

    try:
        with TestClient(app) as client:
            project_url = f"/v1/projects/{project.project_id}"
            collected = client.post(f"{project_url}/evidence", json={})
            assert collected.status_code == 200
            body = collected.json()
            assert body["current_step"] == "evidence_qa"
            assert body["workflow_status"]["evidence_collection"] == "needs_review"
            evidence = body["evidence_collection_artifact"]["task_runs"][0]["evidence"][0]

            reviewed = client.patch(
                f"{project_url}/evidence",
                json={
                    "decisions": [
                        {
                            "evidence_id": evidence["evidence_id"],
                            "status": "accepted",
                            "note": "已核对来源",
                        }
                    ],
                    "confirm": True,
                },
            )
            assert reviewed.status_code == 200
            result = reviewed.json()
            assert result["evidence_collection_artifact"]["human_confirmed"] is True
            assert result["workflow_status"]["evidence_qa"] == "completed"
            assert result["workflow_status"]["industry_analysis"] == "ready"
            assert result["current_step"] == "industry_analysis"

            persisted = client.get(project_url).json()
            assert persisted["evidence_collection_artifact"]["task_runs"][0]["evidence"][0]["reviewer_note"] == "已核对来源"
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
