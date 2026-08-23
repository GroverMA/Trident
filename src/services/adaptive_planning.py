"""Diagnose execution deviation and create human-governed Action Plan revisions."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Any, Mapping, Protocol
from uuid import uuid4

from src.models.feedback import (
    ActionAdjustmentProposal,
    DeviationClass,
    PlanRevisionArtifact,
    ProposalReviewStatus,
)
from src.models.strategy import ActionPlanArtifact
from src.providers.base import ChatMessage, ModelResponse, ProviderError
from src.state.project import ProjectState


class StructuredModel(Protocol):
    def complete_json(
        self, messages: list[ChatMessage], *, enable_thinking: bool = False
    ) -> tuple[dict[str, Any], ModelResponse]: ...


class AdaptivePlanningError(ValueError):
    pass


def _latest_feedback(project: ProjectState) -> dict[str, Any]:
    artifact = project.action_feedback_artifact
    latest: dict[str, Any] = {}
    for entry in artifact.entries if artifact else []:
        current = latest.get(entry.action_id)
        if current is None or entry.submitted_at > current.submitted_at:
            latest[entry.action_id] = entry
    return latest


def _fallback_classification(blockers: str, progress_pct: int) -> DeviationClass:
    text = blockers.lower()
    if any(token in text for token in ("政策", "监管", "市场", "竞争", "客户取消", "external")):
        return DeviationClass.EXTERNAL_CHANGE
    if any(token in text for token in ("资源", "人员", "预算", "执行", "延误")):
        return DeviationClass.EXECUTION_QUALITY
    if progress_pct < 30:
        return DeviationClass.ACTION_DESIGN
    return DeviationClass.DECISION_ASSUMPTION


def _confidence(value: Any) -> int:
    try:
        return max(0, min(100, int(float(value))))
    except (TypeError, ValueError):
        return 65


class AdaptivePlanningService:
    def __init__(self, model: StructuredModel) -> None:
        self.model = model

    def generate(
        self, project: ProjectState, policy: Mapping[str, Any]
    ) -> PlanRevisionArtifact:
        plan = project.action_plan_artifact
        feedback = project.action_feedback_artifact
        if plan is None or not plan.human_confirmed:
            raise AdaptivePlanningError("Action Plan 尚未确认")
        if feedback is None or not feedback.entries:
            raise AdaptivePlanningError("尚无执行反馈，不能进行偏差诊断")
        if feedback.action_plan_id != plan.artifact_id:
            raise AdaptivePlanningError("反馈不属于当前 Action Plan 版本")
        latest = _latest_feedback(project)
        actions = {item.action_id: item for item in plan.actions}
        input_rows = [
            {
                "action_id": action_id,
                "action_title": actions[action_id].title,
                "original_rationale": actions[action_id].rationale,
                "original_timing": actions[action_id].timing,
                "progress_pct": entry.progress_pct,
                "outcome_metrics": entry.outcome_metrics,
                "blockers": entry.blockers,
                "scenario_fields": entry.scenario_fields,
                "feedback_entry_id": entry.entry_id,
            }
            for action_id, entry in latest.items()
            if action_id in actions
        ]
        allowed = policy.get("deviation_classes") or [item.value for item in DeviationClass]
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "你是Trident执行复盘Agent。逐项判断偏差属于给定类别，提出候选调整。"
                    "不得假装调整已经获批，不得删除原计划。只返回JSON："
                    '{"summary":"...","proposals":[{"action_id":"...",'
                    '"deviation_class":"decision_assumption|action_design|execution_quality|external_change",'
                    '"diagnosis":"...","recommendation":"...","proposed_rationale":"...",'
                    '"proposed_timing":"短期|长期|null","confidence":0}]}。'
                ),
            ),
            ChatMessage(
                role="user",
                content=json.dumps({
                    "scenario": project.scenario_pack,
                    "strategy_objective": project.company_strategy_objective,
                    "allowed_deviation_classes": allowed,
                    "feedback": input_rows,
                }, ensure_ascii=False),
            ),
        ]
        payload: dict[str, Any] = {}
        try:
            payload, _ = self.model.complete_json(messages, enable_thinking=True)
        except ProviderError:
            payload = {}
        raw_by_action = {
            str(item.get("action_id")): item
            for item in payload.get("proposals", [])
            if isinstance(item, dict)
        }
        proposals: list[ActionAdjustmentProposal] = []
        for row in input_rows:
            raw = raw_by_action.get(row["action_id"], {})
            deviation_value = str(raw.get("deviation_class", ""))
            try:
                deviation = DeviationClass(deviation_value)
            except ValueError:
                deviation = _fallback_classification(row["blockers"], row["progress_pct"])
            if deviation.value not in allowed:
                deviation = DeviationClass.ACTION_DESIGN
            diagnosis = str(raw.get("diagnosis") or (
                f"当前完成度为{row['progress_pct']}%。"
                + (f"已记录阻塞：{row['blockers']}。" if row["blockers"] else "尚未记录明确阻塞。")
            )).strip()
            recommendation = str(raw.get("recommendation") or (
                "复核行动范围、资源和验证顺序，并以本轮反馈作为下一版本依据。"
            )).strip()
            proposed_rationale = str(raw.get("proposed_rationale") or (
                f"{row['original_rationale']} 本轮执行反馈显示：{diagnosis}"
            )).strip()
            timing = raw.get("proposed_timing")
            proposals.append(ActionAdjustmentProposal(
                action_id=row["action_id"],
                feedback_entry_ids=[row["feedback_entry_id"]],
                deviation_class=deviation,
                diagnosis=diagnosis,
                recommendation=recommendation,
                proposed_rationale=proposed_rationale,
                proposed_timing=timing if timing in {"短期", "长期"} else None,
                confidence=_confidence(raw.get("confidence", 65)),
            ))
        return PlanRevisionArtifact(
            project_id=project.project_id,
            scenario_id=project.scenario_pack,
            base_action_plan_id=plan.artifact_id,
            feedback_artifact_id=feedback.artifact_id,
            proposals=proposals,
            summary=str(payload.get("summary") or "系统已根据最近一次执行反馈形成候选调整，等待人工审核。"),
        )


def review_revision_proposal(
    artifact: PlanRevisionArtifact,
    proposal_id: str,
    status: ProposalReviewStatus,
    note: str | None = None,
) -> PlanRevisionArtifact:
    found = False
    proposals = []
    for item in artifact.proposals:
        if item.proposal_id == proposal_id:
            found = True
            item = item.model_copy(update={
                "review_status": status,
                "reviewer_note": note.strip() if note and note.strip() else None,
                "reviewed_at": datetime.now(UTC),
            })
        proposals.append(item)
    if not found:
        raise AdaptivePlanningError("unknown revision proposal id")
    return artifact.model_copy(update={"proposals": proposals})


def approve_plan_revision(
    project: ProjectState, artifact: PlanRevisionArtifact
) -> tuple[PlanRevisionArtifact, ActionPlanArtifact]:
    plan = project.action_plan_artifact
    if plan is None or plan.artifact_id != artifact.base_action_plan_id:
        raise AdaptivePlanningError("候选调整所依据的 Action Plan 已发生变化")
    if any(item.review_status == ProposalReviewStatus.NEEDS_REVIEW for item in artifact.proposals):
        raise AdaptivePlanningError("仍有候选调整尚未审核")
    accepted = {
        item.action_id: item
        for item in artifact.proposals
        if item.review_status == ProposalReviewStatus.ACCEPTED
    }
    if not accepted:
        raise AdaptivePlanningError("至少接受一项调整后才能创建新版本")
    actions = []
    for action in plan.actions:
        proposal = accepted.get(action.action_id)
        if proposal is None:
            actions.append(action)
            continue
        actions.append(action.model_copy(update={
            "rationale": proposal.proposed_rationale,
            "timing": proposal.proposed_timing or action.timing,
            "reviewer_note": proposal.reviewer_note or "根据执行反馈批准调整",
            "reviewed_at": datetime.now(UTC),
        }))
    revised_plan = plan.model_copy(deep=True, update={
        "artifact_id": f"APL-{uuid4().hex[:10]}",
        "actions": actions,
        "version": plan.version + 1,
        "parent_action_plan_id": plan.artifact_id,
        "revision_note": artifact.summary,
        "updated_at": datetime.now(UTC),
        "confirmed_at": datetime.now(UTC),
        "human_confirmed": True,
    })
    confirmed = artifact.model_copy(update={
        "human_confirmed": True,
        "confirmed_at": datetime.now(UTC),
    })
    return confirmed, revised_plan
