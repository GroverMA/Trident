"""Human-governed routing of continuous-sensing signals."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.knowledge.sop import load_active_sop
from src.models.feedback import EnterpriseTimelineEvent
from src.models.sensing import (
    CandidateGateStatus,
    AssetDraftGateStatus,
    ImpactReviewTarget,
    ImpactReviewTaskStatus,
    SensingImpactReviewTask,
    SensingRevisionCandidate,
    SensingAssetVersionDraft,
    SignalCategory,
    SignalImpactAssessment,
    SignalReviewStatus,
)
from src.state.project import ProjectState
from src.models.research import MarketDefinition, MethodologyTrace, ResearchBriefArtifact, ResearchIntent
from src.models.strategy import ActionPlanArtifact, CompanyScorecardArtifact


def _methodology_trace(artifact_type: str) -> MethodologyTrace:
    sop = load_active_sop()
    return MethodologyTrace(
        sop_id=sop.sop_id,
        sop_name=sop.display_name,
        sop_version=sop.version,
        sop_hash=sop.content_hash,
        locked=sop.locked,
        rule_ids=sop.rule_ids,
        compliance_checks=["持续感知候选保留基准版本", "新资产经独立人工 Gate 后方可生效"],
        skill_versions=sop.skill_versions(artifact_type),
        skill_hashes=sop.skill_hashes(artifact_type),
    )


def _materialize_asset_draft(project: ProjectState, task: SensingImpactReviewTask, candidate: SensingRevisionCandidate) -> SensingAssetVersionDraft:
    now = datetime.now(UTC)
    if task.target == ImpactReviewTarget.RESEARCH_SCOPE:
        current = project.research_brief_artifact
        if current:
            payload = current.model_copy(update={
                "artifact_id": uuid4().hex,
                "information_gaps": [*current.information_gaps, candidate.rationale],
                "clarification_questions": [*current.clarification_questions, *candidate.proposed_changes],
                "generated_at": now,
                "human_confirmed": False,
                "confirmed_at": None,
            }).model_dump(mode="json")
        else:
            payload = ResearchBriefArtifact(
                decision_statement=project.research_objective,
                original_prompt=project.research_objective,
                interpreted_intent=ResearchIntent(
                    interpreted_objective=project.research_objective,
                    requested_topics=[project.industry, project.region],
                    must_answer_questions=[candidate.rationale],
                ),
                market_definition=MarketDefinition(
                    core_market=project.industry,
                    product_scope=project.industry,
                    customer_scope=project.target_company or "该市场的核心客户与采购方",
                    geography_scope=project.region,
                    value_chain_scope="覆盖与当前决策相关的价值链环节",
                    time_scope=project.time_horizon,
                    inclusions=[project.industry],
                    exclusions=["相邻但不属于已确认核心市场的产品与服务"],
                    ambiguities=["该首版范围必须在资产 Gate 中人工校准"],
                ),
                key_questions=[candidate.rationale, *candidate.proposed_changes],
                information_gaps=["尚需结合原研究与新信号补充验证"],
                hypotheses=["该外部信号可能改变当前市场边界或关键假设"],
                clarification_questions=candidate.proposed_changes,
                confidence_note="持续感知生成的首版范围草稿，未经人工确认不得生效。",
                methodology=_methodology_trace("brief"),
            ).model_dump(mode="json")
        proposed_id = str(payload["artifact_id"])
    elif task.target == ImpactReviewTarget.COMPANY_SCORECARD:
        current = project.company_scorecard_artifact
        if current is None:
            raise ValueError("尚无 Company Scorecard 基准资产，请先完成公司评估")
        payload = current.model_copy(update={
            "artifact_id": f"SCR-{uuid4().hex[:10]}",
            "cross_dimension_risks": [*current.cross_dimension_risks, candidate.rationale],
            "updated_at": now,
            "human_confirmed": False,
            "confirmed_at": None,
        }).model_dump(mode="json")
        proposed_id = str(payload["artifact_id"])
    else:
        current = project.action_plan_artifact
        if current is None:
            raise ValueError("尚无 Action Plan 基准资产，请先完成行动计划")
        payload = current.model_copy(update={
            "artifact_id": f"APL-{uuid4().hex[:10]}",
            "version": candidate.proposed_version,
            "parent_action_plan_id": current.artifact_id,
            "revision_note": candidate.rationale,
            "portfolio_risks": [*current.portfolio_risks, candidate.rationale],
            "updated_at": now,
            "human_confirmed": False,
            "confirmed_at": None,
        }).model_dump(mode="json")
        proposed_id = str(payload["artifact_id"])
    return SensingAssetVersionDraft(
        target=task.target,
        base_artifact_id=task.base_artifact_id,
        base_version=task.base_version,
        proposed_artifact_id=proposed_id,
        proposed_version=candidate.proposed_version,
        artifact_payload=payload,
        change_summary=candidate.proposed_changes,
        validation_checks=[
            "完整资产结构校验通过",
            "基准资产与来源信号已保留",
            "场景版本与 Skill 哈希已锁定",
            "当前已批准资产尚未被覆盖",
        ],
    )


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


def _review_task(project: ProjectState, signal_id: str, artifact_id: str, assessment: SignalImpactAssessment) -> SensingImpactReviewTask:
    target = ImpactReviewTarget.RESEARCH_SCOPE
    base_artifact_id = None
    base_version = None
    proposed_version = 1
    if project.action_plan_artifact:
        target = ImpactReviewTarget.ACTION_PLAN
        base_artifact_id = project.action_plan_artifact.artifact_id
        base_version = project.action_plan_artifact.version
        proposed_version = base_version + 1
    elif project.company_scorecard_artifact:
        target = ImpactReviewTarget.COMPANY_SCORECARD
        base_artifact_id = project.company_scorecard_artifact.artifact_id
        base_version = 1
        proposed_version = 2
    elif project.research_brief_artifact:
        base_artifact_id = project.research_brief_artifact.artifact_id
        base_version = 1
        proposed_version = 2
    return SensingImpactReviewTask(
        project_id=project.project_id,
        signal_id=signal_id,
        source_artifact_id=artifact_id,
        target=target,
        affected_assets=assessment.affected_assets,
        affected_hypotheses=assessment.affected_hypotheses,
        recommended_review=assessment.recommended_review,
        base_artifact_id=base_artifact_id,
        base_version=base_version,
        proposed_version=proposed_version,
    )


def _candidate_for(project: ProjectState, task: SensingImpactReviewTask) -> SensingRevisionCandidate:
    artifact = project.continuous_sensing_artifact
    signal = next((item for item in artifact.signals if item.signal_id == task.signal_id), None) if artifact else None
    if signal is None:
        raise ValueError(f"unknown sensing signal: {task.signal_id}")
    artifact_type = {
        ImpactReviewTarget.RESEARCH_SCOPE: "brief",
        ImpactReviewTarget.COMPANY_SCORECARD: "company_assessment",
        ImpactReviewTarget.ACTION_PLAN: "action_plan",
    }[task.target]
    sop = load_active_sop()
    change_map = {
        ImpactReviewTarget.RESEARCH_SCOPE: [
            f"复核市场边界及关键假设：{signal.title}",
            "标记受影响的研究问题，并补充证据时效性检查",
            "保留原研究目标；范围变化须回到 Gate 0 单独确认",
        ],
        ImpactReviewTarget.COMPANY_SCORECARD: [
            f"复核与该信号相关的评分维度：{signal.title}",
            "重新检查外部基准、企业证据与评分差距，不沿用无证据分数",
            "输出原分数、候选分数和变化原因供人工逐项审核",
        ],
        ImpactReviewTarget.ACTION_PLAN: [
            f"复核受影响行动、KPI 与停止条件：{signal.title}",
            "仅提出新增、调整或暂停建议，不改写已批准行动",
            "保留负责人、时间线和原始版本，形成可回滚候选版本",
        ],
    }
    return SensingRevisionCandidate(
        target=task.target,
        proposed_version=task.proposed_version,
        title=f"{task.target.value} 候选 V{task.proposed_version}",
        rationale=task.recommended_review,
        proposed_changes=change_map[task.target],
        retained_constraints=[
            "候选内容不得自动覆盖已批准资产",
            "必须保留来源信号、基准版本与场景版本",
            "必须经过独立 Gate 审核后才能进入后续生成流程",
        ],
        evidence_signal_ids=[signal.signal_id],
        scenario_id=project.scenario_pack,
        scenario_version=project.scenario_pack_version,
        skill_versions=sop.skill_versions(artifact_type),
        skill_hashes=sop.skill_hashes(artifact_type),
    )


def review_sensing_signal(
    project: ProjectState,
    *,
    signal_id: str,
    status: SignalReviewStatus,
    note: str | None = None,
    reviewer: str | None = None,
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
            "is_read": True,
            "read_at": signal.read_at or now,
            "review_status": status,
            "reviewed_by": (reviewer or "").strip() or None,
            "reviewer_note": (note or "").strip() or None,
            "reviewed_at": now,
            "assessment": assessment,
        })
        signals.append(updated)
        accepted_signal = updated if status == SignalReviewStatus.ACCEPTED else None
    if not found:
        raise ValueError(f"unknown sensing signal: {signal_id}")

    timeline = list(project.enterprise_timeline_events)
    tasks = list(artifact.review_tasks)
    if accepted_signal and not any(signal_id in event.artifact_ids for event in timeline):
        assessment = accepted_signal.assessment
        if assessment and not any(task.signal_id == signal_id for task in tasks):
            tasks.append(_review_task(project, signal_id, artifact.artifact_id, assessment))
        timeline.append(EnterpriseTimelineEvent(
            event_type="sensing_signal_accepted",
            project_id=project.project_id,
            scenario_id=project.scenario_pack,
            title=f"外部信号已接受：{accepted_signal.title}",
            summary=(assessment.recommended_review if assessment else accepted_signal.impact_reason),
            artifact_ids=[artifact.artifact_id, signal_id],
        ))

    return project.model_copy(update={
        "continuous_sensing_artifact": artifact.model_copy(update={"signals": signals, "review_tasks": tasks}),
        "enterprise_timeline_events": timeline,
    })


def update_sensing_inbox(
    project: ProjectState,
    *,
    signal_ids: list[str],
    status: SignalReviewStatus | None = None,
    note: str | None = None,
    reviewer: str | None = None,
) -> ProjectState:
    """Mark signals read or apply one governed review decision to a selection."""
    unique_ids = list(dict.fromkeys(item.strip() for item in signal_ids if item.strip()))
    if not unique_ids:
        raise ValueError("请至少选择一条感知信号")
    artifact = project.continuous_sensing_artifact
    if artifact is None:
        raise ValueError("当前项目尚无持续感知信号")
    known_ids = {signal.signal_id for signal in artifact.signals}
    missing = [signal_id for signal_id in unique_ids if signal_id not in known_ids]
    if missing:
        raise ValueError(f"unknown sensing signals: {', '.join(missing)}")

    current = project
    if status is not None:
        if status == SignalReviewStatus.NEEDS_REVIEW:
            raise ValueError("批量审核必须选择接受或忽略")
        for signal_id in unique_ids:
            current = review_sensing_signal(
                current,
                signal_id=signal_id,
                status=status,
                note=note,
                reviewer=reviewer,
            )
        return current

    now = datetime.now(UTC)
    current_artifact = current.continuous_sensing_artifact
    return current.model_copy(update={
        "continuous_sensing_artifact": current_artifact.model_copy(update={
            "signals": [
                signal.model_copy(update={"is_read": True, "read_at": signal.read_at or now})
                if signal.signal_id in unique_ids else signal
                for signal in current_artifact.signals
            ]
        }),
        "updated_at": now,
    })


def review_sensing_impact_task(
    project: ProjectState,
    *,
    task_id: str,
    status: ImpactReviewTaskStatus,
    note: str | None = None,
) -> ProjectState:
    artifact = project.continuous_sensing_artifact
    if artifact is None:
        raise ValueError("当前项目尚无持续感知复核任务")
    if status == ImpactReviewTaskStatus.NEEDS_REVIEW:
        raise ValueError("复核任务必须选择批准生成候选版本或关闭")
    now = datetime.now(UTC)
    found = None
    tasks = []
    for task in artifact.review_tasks:
        if task.task_id != task_id:
            tasks.append(task)
            continue
        found = task.model_copy(update={
            "status": status,
            "reviewer_note": (note or "").strip() or None,
            "reviewed_at": now,
            "candidate": (_candidate_for(project, task) if status == ImpactReviewTaskStatus.APPROVED_FOR_REVISION else task.candidate),
        })
        tasks.append(found)
    if found is None:
        raise ValueError(f"unknown sensing review task: {task_id}")

    timeline = list(project.enterprise_timeline_events)
    event_type = "sensing_revision_authorized" if status == ImpactReviewTaskStatus.APPROVED_FOR_REVISION else "sensing_revision_dismissed"
    if not any(task_id in event.artifact_ids for event in timeline):
        timeline.append(EnterpriseTimelineEvent(
            event_type=event_type,
            project_id=project.project_id,
            scenario_id=project.scenario_pack,
            title=("已批准生成候选版本" if status == ImpactReviewTaskStatus.APPROVED_FOR_REVISION else "已关闭信号影响复核"),
            summary=found.recommended_review,
            artifact_ids=[artifact.artifact_id, found.signal_id, task_id],
        ))
    return project.model_copy(update={
        "continuous_sensing_artifact": artifact.model_copy(update={"review_tasks": tasks}),
        "enterprise_timeline_events": timeline,
    })


def review_sensing_revision_candidate(
    project: ProjectState,
    *,
    task_id: str,
    status: CandidateGateStatus,
    note: str | None = None,
) -> ProjectState:
    if status not in {CandidateGateStatus.APPROVED, CandidateGateStatus.REJECTED}:
        raise ValueError("候选版本 Gate 必须选择批准或退回")
    artifact = project.continuous_sensing_artifact
    if artifact is None:
        raise ValueError("当前项目尚无持续感知复核任务")
    now = datetime.now(UTC)
    reviewed_task = None
    tasks = []
    for task in artifact.review_tasks:
        if task.task_id != task_id:
            tasks.append(task)
            continue
        if task.candidate is None:
            raise ValueError("该复核任务尚未生成候选版本")
        candidate = task.candidate.model_copy(update={
                "gate_status": status,
                "gate_note": (note or "").strip() or None,
                "reviewed_at": now,
            })
        if status == CandidateGateStatus.APPROVED:
            candidate = candidate.model_copy(update={"asset_draft": _materialize_asset_draft(project, task, candidate)})
        reviewed_task = task.model_copy(update={
            "candidate": candidate
        })
        tasks.append(reviewed_task)
    if reviewed_task is None:
        raise ValueError(f"unknown sensing review task: {task_id}")
    candidate = reviewed_task.candidate
    timeline = list(project.enterprise_timeline_events)
    event_type = "sensing_candidate_approved" if status == CandidateGateStatus.APPROVED else "sensing_candidate_rejected"
    if not any(candidate.candidate_id in event.artifact_ids for event in timeline):
        timeline.append(EnterpriseTimelineEvent(
            event_type=event_type,
            project_id=project.project_id,
            scenario_id=project.scenario_pack,
            title=("候选版本已通过 Gate" if status == CandidateGateStatus.APPROVED else "候选版本已退回"),
            summary=candidate.rationale,
            artifact_ids=[artifact.artifact_id, reviewed_task.signal_id, task_id, candidate.candidate_id],
        ))
    return project.model_copy(update={
        "continuous_sensing_artifact": artifact.model_copy(update={"review_tasks": tasks}),
        "enterprise_timeline_events": timeline,
    })


def review_sensing_asset_draft(
    project: ProjectState,
    *,
    task_id: str,
    status: AssetDraftGateStatus,
    note: str | None = None,
) -> ProjectState:
    if status not in {AssetDraftGateStatus.ACTIVATED, AssetDraftGateStatus.REJECTED}:
        raise ValueError("资产 Gate 必须选择启用或退回")
    artifact = project.continuous_sensing_artifact
    if artifact is None:
        raise ValueError("当前项目尚无持续感知复核任务")
    now = datetime.now(UTC)
    reviewed_task = None
    tasks = []
    updates: dict[str, object] = {}
    for task in artifact.review_tasks:
        if task.task_id != task_id:
            tasks.append(task)
            continue
        if task.candidate is None or task.candidate.asset_draft is None:
            raise ValueError("该候选尚未生成完整资产草稿")
        draft = task.candidate.asset_draft.model_copy(update={
            "gate_status": status,
            "gate_note": (note or "").strip() or None,
            "reviewed_at": now,
        })
        if status == AssetDraftGateStatus.ACTIVATED:
            payload = draft.artifact_payload
            if draft.target == ImpactReviewTarget.RESEARCH_SCOPE:
                new_asset = ResearchBriefArtifact.model_validate(payload).model_copy(update={"human_confirmed": True, "confirmed_at": now})
                updates["research_brief_history"] = [*project.research_brief_history, *([project.research_brief_artifact] if project.research_brief_artifact else [])]
                updates["research_brief_artifact"] = new_asset
                updates["market_scope_confirmed_at"] = now
            elif draft.target == ImpactReviewTarget.COMPANY_SCORECARD:
                new_asset = CompanyScorecardArtifact.model_validate(payload).model_copy(update={"human_confirmed": True, "confirmed_at": now})
                updates["company_scorecard_history"] = [*project.company_scorecard_history, *([project.company_scorecard_artifact] if project.company_scorecard_artifact else [])]
                updates["company_scorecard_artifact"] = new_asset
            else:
                new_asset = ActionPlanArtifact.model_validate(payload).model_copy(update={"human_confirmed": True, "confirmed_at": now})
                updates["action_plan_history"] = [*project.action_plan_history, *([project.action_plan_artifact] if project.action_plan_artifact else [])]
                updates["action_plan_artifact"] = new_asset
        reviewed_task = task.model_copy(update={"candidate": task.candidate.model_copy(update={"asset_draft": draft})})
        tasks.append(reviewed_task)
    if reviewed_task is None:
        raise ValueError(f"unknown sensing review task: {task_id}")
    draft = reviewed_task.candidate.asset_draft
    timeline = list(project.enterprise_timeline_events)
    timeline.append(EnterpriseTimelineEvent(
        event_type="sensing_asset_activated" if status == AssetDraftGateStatus.ACTIVATED else "sensing_asset_rejected",
        project_id=project.project_id,
        scenario_id=project.scenario_pack,
        title="感知资产新版本已启用" if status == AssetDraftGateStatus.ACTIVATED else "感知资产草稿已退回",
        summary=draft.gate_note or reviewed_task.candidate.rationale,
        artifact_ids=[artifact.artifact_id, task_id, reviewed_task.candidate.candidate_id, draft.draft_id, draft.proposed_artifact_id],
    ))
    return project.model_copy(update={
        **updates,
        "continuous_sensing_artifact": artifact.model_copy(update={"review_tasks": tasks}),
        "enterprise_timeline_events": timeline,
        "updated_at": now,
    })
