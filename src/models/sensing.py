"""Continuous-sensing artifacts kept separate from reviewed research evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class SignalCategory(StrEnum):
    POLICY = "policy"
    COMPETITION = "competition"
    CUSTOMER = "customer"
    TECHNOLOGY = "technology"
    OPERATIONS = "operations"
    OTHER = "other"


class SignalImpact(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    REVIEW = "review"


class SignalReviewStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    ACCEPTED = "accepted"
    IGNORED = "ignored"


class ImpactReviewTaskStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    APPROVED_FOR_REVISION = "approved_for_revision"
    DISMISSED = "dismissed"


class CandidateGateStatus(StrEnum):
    NOT_GENERATED = "not_generated"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class AssetDraftGateStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    ACTIVATED = "activated"
    REJECTED = "rejected"


class SensingCadence(StrEnum):
    MANUAL = "manual"
    DAILY = "daily"
    WEEKLY = "weekly"


class SensingRunStatus(StrEnum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class SensingSourceType(StrEnum):
    NEWS_AGGREGATOR = "news_aggregator"
    COMPANY_OFFICIAL = "company_official"
    REGULATOR_GOVERNMENT = "regulator_government"
    EXCHANGE_DISCLOSURE = "exchange_disclosure"
    PROFESSIONAL_MEDIA = "professional_media"
    INTERNAL_KPI = "internal_kpi"


class SensingSourceStatus(StrEnum):
    READY = "ready"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SensingSourceFormat(StrEnum):
    AUTO = "auto"
    RSS = "rss"
    HTML = "html"


class ImpactReviewTarget(StrEnum):
    RESEARCH_SCOPE = "research_scope"
    COMPANY_SCORECARD = "company_scorecard"
    ACTION_PLAN = "action_plan"


class KpiDirection(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class InternalKpiObservation(BaseModel):
    metric_name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    period: str = Field(min_length=1)
    direction: KpiDirection = KpiDirection.HIGHER_IS_BETTER
    comparison_value: float | None = None
    target_value: float | None = None
    note: str = ""
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class KpiConnectorStatus(StrEnum):
    READY = "ready"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class KpiFieldMapping(BaseModel):
    metric_name: str = "指标名称"
    value: str = "本期数值"
    unit: str = "单位"
    period: str = "期间"
    direction: str = "判断方向"
    comparison_value: str = "上期值"
    target_value: str = "目标值"
    note: str = "经营说明"


class FeishuKpiConnector(BaseModel):
    connector_id: str = Field(default_factory=lambda: f"KCO-{uuid4().hex[:10]}")
    name: str = "飞书经营 KPI"
    app_token: str = Field(min_length=1)
    table_id: str = Field(min_length=1)
    view_id: str | None = None
    field_mapping: KpiFieldMapping = Field(default_factory=KpiFieldMapping)
    status: KpiConnectorStatus = KpiConnectorStatus.READY
    last_synced_at: datetime | None = None
    last_record_count: int = Field(default=0, ge=0)
    last_error: str | None = None


class SignalImpactAssessment(BaseModel):
    affected_assets: list[str] = Field(default_factory=list)
    affected_hypotheses: list[str] = Field(default_factory=list)
    recommended_review: str
    confidence: int = Field(ge=0, le=100)


class SensingAssetVersionDraft(BaseModel):
    draft_id: str = Field(default_factory=lambda: f"SAD-{uuid4().hex[:10]}")
    target: ImpactReviewTarget
    base_artifact_id: str | None = None
    base_version: int | None = Field(default=None, ge=1)
    proposed_artifact_id: str
    proposed_version: int = Field(ge=1)
    artifact_payload: dict[str, object]
    change_summary: list[str] = Field(min_length=1)
    validation_checks: list[str] = Field(min_length=1)
    gate_status: AssetDraftGateStatus = AssetDraftGateStatus.NEEDS_REVIEW
    gate_note: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None


class SensingRevisionCandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: f"SRC-{uuid4().hex[:10]}")
    target: ImpactReviewTarget
    proposed_version: int = Field(ge=1)
    title: str
    rationale: str
    proposed_changes: list[str] = Field(min_length=1)
    retained_constraints: list[str] = Field(min_length=1)
    evidence_signal_ids: list[str] = Field(min_length=1)
    scenario_id: str
    scenario_version: str
    skill_versions: dict[str, str] = Field(default_factory=dict)
    skill_hashes: dict[str, str] = Field(default_factory=dict)
    gate_status: CandidateGateStatus = CandidateGateStatus.NEEDS_REVIEW
    gate_note: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None
    asset_draft: SensingAssetVersionDraft | None = None


class SensingSignal(BaseModel):
    signal_id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    summary: str = ""
    url: HttpUrl
    source: str
    source_id: str | None = None
    source_type: SensingSourceType = SensingSourceType.NEWS_AGGREGATOR
    source_tier: int = Field(default=3, ge=1, le=4)
    published_at: datetime | None = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    category: SignalCategory = SignalCategory.OTHER
    impact: SignalImpact = SignalImpact.REVIEW
    impact_reason: str
    matched_terms: list[str] = Field(default_factory=list)
    relevance_score: int = Field(ge=0, le=100)
    project_id: str
    is_read: bool = False
    read_at: datetime | None = None
    review_status: SignalReviewStatus = SignalReviewStatus.NEEDS_REVIEW
    reviewed_by: str | None = None
    reviewer_note: str | None = None
    reviewed_at: datetime | None = None
    assessment: SignalImpactAssessment | None = None
    kpi_observation: InternalKpiObservation | None = None


class SensingImpactReviewTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"SRT-{uuid4().hex[:10]}")
    project_id: str
    signal_id: str
    source_artifact_id: str
    target: ImpactReviewTarget
    affected_assets: list[str] = Field(min_length=1)
    affected_hypotheses: list[str] = Field(default_factory=list)
    recommended_review: str
    base_artifact_id: str | None = None
    base_version: int | None = Field(default=None, ge=1)
    proposed_version: int = Field(default=1, ge=1)
    status: ImpactReviewTaskStatus = ImpactReviewTaskStatus.NEEDS_REVIEW
    reviewer_note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None
    candidate: SensingRevisionCandidate | None = None


class SensingSubscription(BaseModel):
    enabled: bool = False
    cadence: SensingCadence = SensingCadence.MANUAL
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    last_run_status: SensingRunStatus | None = None
    last_run_error: str | None = None


class SensingManagementDigest(BaseModel):
    headline: str
    summary: str
    high_impact_count: int = Field(ge=0)
    pending_review_count: int = Field(ge=0)
    new_signal_count: int = Field(ge=0)
    top_signal_ids: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SensingSourceDefinition(BaseModel):
    source_id: str = Field(default_factory=lambda: f"SSO-{uuid4().hex[:10]}")
    name: str
    source_type: SensingSourceType
    source_format: SensingSourceFormat = SensingSourceFormat.AUTO
    tier: int = Field(ge=1, le=4)
    url: HttpUrl
    enabled: bool = True
    status: SensingSourceStatus = SensingSourceStatus.READY
    last_checked_at: datetime | None = None
    last_error: str | None = None


class ContinuousSensingArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    project_id: str
    watch_terms: list[str]
    feed_urls: list[str] = Field(default_factory=list)
    sources: list[SensingSourceDefinition] = Field(default_factory=list)
    kpi_connectors: list[FeishuKpiConnector] = Field(default_factory=list)
    signals: list[SensingSignal] = Field(default_factory=list)
    review_tasks: list[SensingImpactReviewTask] = Field(default_factory=list)
    subscription: SensingSubscription = Field(default_factory=SensingSubscription)
    management_digest: SensingManagementDigest | None = None
    fetch_errors: list[str] = Field(default_factory=list)
    refreshed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
