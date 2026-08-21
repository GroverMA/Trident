from fastapi.testclient import TestClient

from src.api.app import app, get_research_application
from src.application.research import ResearchApplication
from src.persistence.sqlite_projects import SQLiteProjectRepository


def test_scenario_interview_persists_and_generates_sourced_profile(tmp_path) -> None:
    research = ResearchApplication(
        projects=SQLiteProjectRepository(tmp_path / "interview.db"),
        service_factory=lambda: (_ for _ in ()).throw(
            AssertionError("diagnostic interview must not require AI runtime")
        ),
    )
    app.dependency_overrides[get_research_application] = lambda: research
    payload = {
        "project_name": "示例企业增长决策",
        "industry": "工业机器人",
        "region": "中国",
        "research_objective": "寻找第二增长曲线",
        "time_horizon": "未来3年",
        "target_company": "示例企业",
        "company_strategy_enabled": True,
        "company_strategy_objective": "三年销售额翻倍",
        "workspace_mode": "analyst_workspace",
        "scenario_pack": "growth_strategy",
        "scenario_pack_version": "1.0.0",
    }
    try:
        with TestClient(app) as client:
            created = client.post("/v1/projects", json=payload).json()
            project_id = created["project_id"]
            started = client.post(
                f"/v1/projects/{project_id}/interview/start", json={"restart": False}
            )
            assert started.status_code == 200
            first = started.json()["interview_session_artifact"]
            assert first["turns"][0]["topic_id"] == "performance_change"

            answers = [
                "过去一年收入增长百分之十，订单数据每月复盘。",
                "目前最大客户占收入约三成，渠道集中度较高。",
                "管理层会先看财务指标，再由负责人快速拍板试错。",
                "最缺少新行业客户资源和可以复制的销售团队。",
            ]
            latest = None
            for answer in answers:
                response = client.post(
                    f"/v1/projects/{project_id}/interview/answer",
                    json={"answer": answer},
                )
                assert response.status_code == 200
                latest = response.json()

            assert latest is not None
            assert latest["interview_session_artifact"]["status"] == "completed"
            profile = latest["entity_profile_artifact"]
            assert profile["entity_name"] == "示例企业"
            assert len(profile["source_turn_ids"]) == 4

            restored = client.get(f"/v1/projects/{project_id}").json()
            assert restored["entity_profile_artifact"]["artifact_id"] == profile["artifact_id"]
            assert len(restored["interview_session_artifact"]["turns"]) == 4
    finally:
        app.dependency_overrides.clear()
