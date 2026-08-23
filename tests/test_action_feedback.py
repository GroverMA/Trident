import src.api.app  # noqa: F401 - initialize the existing service container import order

from src.models.strategy import ActionPlanArtifact, StrategicAction, StrategyReviewStatus
from src.services.action_feedback import build_feedback_dashboard, submit_action_feedback
from src.state.project import ProjectState


def _project() -> ProjectState:
    action = StrategicAction.model_construct(
        action_id="ACT-1",
        title="验证重点客户",
        review_status=StrategyReviewStatus.ACCEPTED,
    )
    plan = ActionPlanArtifact.model_construct(
        artifact_id="APL-1",
        project_id="project-1",
        actions=[action],
        human_confirmed=True,
    )
    return ProjectState(
        project_id="project-1",
        project_name="增长项目",
        industry="工业软件",
        region="中国",
        target_company="示例企业",
        company_strategy_enabled=True,
        company_strategy_objective="寻找第二增长曲线",
        research_objective="识别增长机会",
        time_horizon="2026-2030",
        scenario_pack="growth_strategy",
    ).model_copy(update={"action_plan_artifact": plan})


def test_feedback_uses_scenario_fields_and_versions_history() -> None:
    project = _project()
    policy = {
        "enabled": True,
        "feedback_fields": ["progress_pct", "outcome_metrics", "customer_feedback", "blockers"],
    }
    first = submit_action_feedback(
        project,
        policy,
        action_id="ACT-1",
        progress_pct=25,
        scenario_fields={"customer_feedback": "客户愿意进入试点"},
    )
    second = submit_action_feedback(
        project.model_copy(update={"action_feedback_artifact": first}),
        policy,
        action_id="ACT-1",
        progress_pct=60,
        outcome_metrics="完成两家试点",
        blockers="采购周期延长",
    )
    assert second.version == 2
    assert len(second.entries) == 2
    assert second.entries[0].scenario_fields["customer_feedback"] == "客户愿意进入试点"

    dashboard = build_feedback_dashboard(project.model_copy(update={"action_feedback_artifact": second}))
    assert dashboard.coverage_pct == 100
    assert dashboard.average_progress_pct == 60
    assert dashboard.blocker_count == 1
    assert dashboard.adjustment_required is True


def test_feedback_rejects_fields_outside_scenario_contract() -> None:
    project = _project()
    try:
        submit_action_feedback(
            project,
            {"enabled": True, "feedback_fields": ["progress_pct"]},
            action_id="ACT-1",
            progress_pct=10,
            scenario_fields={"founder_feedback": "not a growth field"},
        )
    except ValueError as exc:
        assert "不支持反馈字段" in str(exc)
    else:
        raise AssertionError("unknown scenario field should fail")
