"""Scenario-contract driven action feedback without silent plan mutation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from src.models.feedback import ActionFeedbackArtifact, ActionFeedbackEntry, FeedbackDashboard
from src.models.strategy import StrategyReviewStatus
from src.state.project import ProjectState


RESERVED_FIELDS = {"progress_pct", "outcome_metrics", "blockers", "evidence_refs"}


def submit_action_feedback(
    project: ProjectState,
    policy: Mapping[str, Any],
    *,
    action_id: str,
    progress_pct: int,
    outcome_metrics: str = "",
    blockers: str = "",
    evidence_refs: list[str] | None = None,
    scenario_fields: Mapping[str, str] | None = None,
) -> ActionFeedbackArtifact:
    plan = project.action_plan_artifact
    if not project.company_strategy_enabled or not policy.get("enabled"):
        raise ValueError("当前场景未启用行动反馈")
    if plan is None or not plan.human_confirmed:
        raise ValueError("Action Plan 尚未确认，不能写入执行反馈")
    accepted_ids = {
        action.action_id
        for action in plan.actions
        if action.review_status == StrategyReviewStatus.ACCEPTED
    }
    if action_id not in accepted_ids:
        raise ValueError("反馈必须关联已接受的行动项")

    allowed = set(policy.get("feedback_fields", ())) - RESERVED_FIELDS
    fields = {
        key: str(value).strip()
        for key, value in (scenario_fields or {}).items()
        if key in allowed and str(value).strip()
    }
    unknown = set(scenario_fields or {}) - allowed
    if unknown:
        raise ValueError(f"当前场景不支持反馈字段: {', '.join(sorted(unknown))}")

    entry = ActionFeedbackEntry(
        action_id=action_id,
        progress_pct=progress_pct,
        outcome_metrics=outcome_metrics.strip(),
        blockers=blockers.strip(),
        evidence_refs=[item.strip() for item in (evidence_refs or []) if item.strip()],
        scenario_fields=fields,
    )
    current = project.action_feedback_artifact
    entries = [*(current.entries if current and current.action_plan_id == plan.artifact_id else []), entry]
    artifact_payload: dict[str, Any] = {
        "project_id": project.project_id,
        "scenario_id": project.scenario_pack,
        "action_plan_id": plan.artifact_id,
        "entries": entries,
        "version": (current.version + 1) if current and current.action_plan_id == plan.artifact_id else 1,
        "updated_at": datetime.now(UTC),
    }
    if current and current.action_plan_id == plan.artifact_id:
        artifact_payload["artifact_id"] = current.artifact_id
    return ActionFeedbackArtifact(**artifact_payload)


def build_feedback_dashboard(project: ProjectState) -> FeedbackDashboard:
    plan = project.action_plan_artifact
    actions = [
        item for item in (plan.actions if plan else [])
        if item.review_status == StrategyReviewStatus.ACCEPTED
    ]
    entries = project.action_feedback_artifact.entries if project.action_feedback_artifact else []
    latest: dict[str, ActionFeedbackEntry] = {}
    for entry in entries:
        if entry.action_id not in latest or entry.submitted_at > latest[entry.action_id].submitted_at:
            latest[entry.action_id] = entry
    count = len(actions)
    progress = round(sum(item.progress_pct for item in latest.values()) / len(latest)) if latest else 0
    blocker_count = sum(bool(item.blockers.strip()) for item in latest.values())
    return FeedbackDashboard(
        action_count=count,
        actions_with_feedback=len(latest),
        coverage_pct=round(len(latest) / count * 100) if count else 0,
        average_progress_pct=progress,
        blocker_count=blocker_count,
        adjustment_required=blocker_count > 0 or any(item.progress_pct < 30 for item in latest.values()),
        last_feedback_at=max((item.submitted_at for item in entries), default=None),
    )
