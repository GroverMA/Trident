"""Human-governed routing of continuous-sensing signals."""

from __future__ import annotations

from datetime import UTC, datetime

from src.models.feedback import EnterpriseTimelineEvent
from src.models.sensing import (
    SignalCategory,
    SignalImpactAssessment,
    SignalReviewStatus,
)
from src.state.project import ProjectState


def _assess(project: ProjectState, category: SignalCategory) -> SignalImpactAssessment:
    assets = ["research_scope"]
    recommendation = "复核研究范围、关键假设和证据时效性"
    if project.company_scorecard_artifact:
        assets.append("company_scorecard")
    if project.action_plan_artifact:
        assets.append("action_plan")
    if category in {SignalCategory.COMPETITION, SignalCategory.TECHNOLOGY}:
        recommendation = "复核竞争格局、技术替代假设和机会优先级"
    elif category == SignalCategory.POLICY:
        recommendation = "复核市场边界、准入条件、政策适用范围和生效时间"
    elif category == SignalCategory.CUSTOMER:
        recommendation = "复核客户需求、采购门槛、收入假设和验证行动"
    elif category == SignalCategory.OPERATIONS:
        recommendation = "复核经营基线、执行偏差和 Action Plan 指标"

    hypotheses = (
        project.research_brief_artifact.hypotheses[:5]
        if project.research_brief_artifact
        else []
    )
    return SignalImpactAssessment(
        affected_assets=assets,
        affected_hypotheses=hypotheses,
        recommended_review=recommendation,
        confidence=80 if category != SignalCategory.OTHER else 60,
    )


def review_sensing_signal(
    project: ProjectState,
    *,
    signal_id: str,
    status: SignalReviewStatus,
    note: str | None = None,
) -> ProjectState:
    artifact = project.continuous_sensing_artifact
    if artifact is None:
        raise ValueError("当前项目尚无持续感知信号")
    if status == SignalReviewStatus.NEEDS_REVIEW:
        raise ValueError("人工审核必须选择接受或忽略")

    found = False
    accepted_signal = None
    signals = []
    now = datetime.now(UTC)
    for signal in artifact.signals:
        if signal.signal_id != signal_id:
            signals.append(signal)
            continue
        found = True
        assessment = _assess(project, signal.category) if status == SignalReviewStatus.ACCEPTED else None
        updated = signal.model_copy(update={
            "review_status": status,
            "reviewer_note": (note or "").strip() or None,
            "reviewed_at": now,
            "assessment": assessment,
        })
        signals.append(updated)
        accepted_signal = updated if status == SignalReviewStatus.ACCEPTED else None
    if not found:
        raise ValueError(f"unknown sensing signal: {signal_id}")

    timeline = list(project.enterprise_timeline_events)
    if accepted_signal and not any(signal_id in event.artifact_ids for event in timeline):
        assessment = accepted_signal.assessment
        timeline.append(EnterpriseTimelineEvent(
            event_type="sensing_signal_accepted",
            project_id=project.project_id,
            scenario_id=project.scenario_pack,
            title=f"外部信号已接受：{accepted_signal.title}",
            summary=(assessment.recommended_review if assessment else accepted_signal.impact_reason),
            artifact_ids=[artifact.artifact_id, signal_id],
        ))

    return project.model_copy(update={
        "continuous_sensing_artifact": artifact.model_copy(update={"signals": signals}),
        "enterprise_timeline_events": timeline,
    })
