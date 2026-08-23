import pytest

import src.api.app  # noqa: F401 - initialize the existing service container import order

from src.models.feedback import ProposalReviewStatus
from src.models.strategy import ActionPlanArtifact, StrategicAction, StrategyReviewStatus
from src.providers.base import ModelResponse
from src.services.action_feedback import submit_action_feedback
from src.services.adaptive_planning import (
    AdaptivePlanningError,
    AdaptivePlanningService,
    approve_plan_revision,
    review_revision_proposal,
)
from src.state.project import ProjectState


class RevisionModel:
    def complete_json(self, messages, *, enable_thinking=False):
        return ({
            "summary": "客户验证延后，需要调整验证节奏。",
            "proposals": [{
                "action_id": "ACT-1",
                "deviation_class": "execution_quality",
                "diagnosis": "采购周期长于原假设。",
                "recommendation": "把一次验收拆为两个验证里程碑。",
                "proposed_rationale": "先验证技术适配，再验证商业采购。",
                "proposed_timing": "短期",
                "confidence": 82,
            }],
        }, ModelResponse(content="{}"))


def _project() -> ProjectState:
    action = StrategicAction.model_construct(
        action_id="ACT-1",
        title="验证重点客户",
        rationale="在30天内完成客户验证",
        owner_role="增长负责人",
        timing="短期",
        review_status=StrategyReviewStatus.ACCEPTED,
    )
    plan = ActionPlanArtifact.model_construct(
        artifact_id="APL-1",
        project_id="project-1",
        actions=[action],
        human_confirmed=True,
        version=1,
    )
    project = ProjectState(
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
    feedback = submit_action_feedback(
        project,
        {"enabled": True, "feedback_fields": ["progress_pct", "outcome_metrics", "blockers"]},
        action_id="ACT-1",
        progress_pct=35,
        outcome_metrics="已完成技术交流",
        blockers="客户采购周期延长",
    )
    return project.model_copy(update={"action_feedback_artifact": feedback})


def test_revision_requires_human_review_and_preserves_original_plan() -> None:
    project = _project()
    original = project.action_plan_artifact.model_copy(deep=True)
    artifact = AdaptivePlanningService(RevisionModel()).generate(
        project, {"deviation_classes": ["execution_quality", "action_design"]}
    )

    with pytest.raises(AdaptivePlanningError, match="尚未审核"):
        approve_plan_revision(project, artifact)

    reviewed = review_revision_proposal(
        artifact,
        artifact.proposals[0].proposal_id,
        ProposalReviewStatus.ACCEPTED,
        "批准分阶段验证",
    )
    confirmed, revised = approve_plan_revision(project, reviewed)

    assert confirmed.human_confirmed is True
    assert revised.version == 2
    assert revised.parent_action_plan_id == "APL-1"
    assert revised.actions[0].rationale == "先验证技术适配，再验证商业采购。"
    assert project.action_plan_artifact == original


def test_revision_cannot_create_version_when_all_candidates_rejected() -> None:
    project = _project()
    artifact = AdaptivePlanningService(RevisionModel()).generate(project, {})
    reviewed = review_revision_proposal(
        artifact,
        artifact.proposals[0].proposal_id,
        ProposalReviewStatus.REJECTED,
    )
    with pytest.raises(AdaptivePlanningError, match="至少接受一项"):
        approve_plan_revision(project, reviewed)
