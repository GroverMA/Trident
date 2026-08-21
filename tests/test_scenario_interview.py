import json

from fastapi.testclient import TestClient

from src.api.app import app, get_research_application
from src.application.research import ResearchApplication
from src.persistence.sqlite_projects import SQLiteProjectRepository
from src.core.registry import ExtensionRegistry
from src.scenarios import builtin_scenario_packs
from src.services.scenario_interview import ScenarioInterviewService
from src.state.project import ProjectState


class AdaptiveInterviewModel:
    def complete_json(self, messages, *, enable_thinking=False):
        answer = json.loads(messages[-1].content)["answer"]
        if "大概" in answer:
            return ({
                "summary": "用户只给出了方向性判断。",
                "extracted_facts": [],
                "ambiguities": ["缺少变化幅度"],
                "missing_information": ["收入或利润的具体范围"],
                "answer_quality": "needs_validation",
                "topic_complete": False,
                "follow_up_question": "大概变化了多少？如果没有精确数，给一个区间也可以。",
                "confidence": 0.42,
            }, object())
        return ({
            "summary": "回答包含可继续研究的具体信息。",
            "extracted_facts": ["收入增长约10%"],
            "ambiguities": [],
            "missing_information": [],
            "answer_quality": "sufficient",
            "topic_complete": True,
            "follow_up_question": None,
            "confidence": 0.8,
        }, object())


def test_interview_analyses_answer_before_moving_to_next_topic() -> None:
    service = ScenarioInterviewService(
        ExtensionRegistry(builtin_scenario_packs()),
        model_factory=AdaptiveInterviewModel,
    )
    project = ProjectState(
        project_name="动态访谈",
        industry="工业机器人",
        region="中国",
        research_objective="寻找增长机会",
        time_horizon="未来3年",
        target_company="示例企业",
        scenario_pack="growth_strategy",
        scenario_pack_version="1.0.0",
    )
    started = service.start(project)
    followed_up = service.answer(started, "收入大概增长了一些")
    session = followed_up.interview_session_artifact
    assert session is not None
    assert session.turns[-1].topic_id == "performance_change"
    assert session.turns[-1].question.startswith("大概变化了多少")
    assert session.turns[0].analysis is not None
    assert session.turns[0].analysis.ambiguities == ["缺少变化幅度"]

    advanced = service.answer(followed_up, "收入同比增长约10%，来自月度财务报表。")
    advanced_session = advanced.interview_session_artifact
    assert advanced_session is not None
    assert advanced_session.turns[-1].topic_id == "concentration_risk"


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
            assert profile["human_confirmed"] is False

            confirmed = client.patch(
                f"/v1/projects/{project_id}/interview/profile",
                json={
                    "operating_portrait": profile["operating_portrait"],
                    "decision_style": profile["decision_style"],
                    "research_next_step": profile["research_next_step"],
                    "confirm": True,
                },
            )
            assert confirmed.status_code == 200
            confirmed_profile = confirmed.json()["entity_profile_artifact"]
            assert confirmed_profile["human_confirmed"] is True
            assert confirmed_profile["confirmed_at"] is not None

            restored = client.get(f"/v1/projects/{project_id}").json()
            assert restored["entity_profile_artifact"]["artifact_id"] == profile["artifact_id"]
            assert restored["entity_profile_artifact"]["human_confirmed"] is True
            assert len(restored["interview_session_artifact"]["turns"]) == 4
    finally:
        app.dependency_overrides.clear()
