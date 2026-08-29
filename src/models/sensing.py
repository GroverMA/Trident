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


class ImpactReviewTarget(StrEnum):
    RESEARCH_SCOPE = "research_scope"
    COMPANY_SCORECARD = "company_scorecard"
    ACTION_PLAN = "action_plan"


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
    published_at: datetime | None = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    category: SignalCategory = SignalCategory.OTHER
    impact: SignalImpact = SignalImpact.REVIEW
    impact_reason: str
    matched_terms: list[str] = Field(default_factory=list)
    relevance_score: int = Field(ge=0, le=100)
    project_id: str
    review_status: SignalReviewStatus = SignalReviewStatus.NEEDS_REVIEW
    reviewer_note: str | None = None
    reviewed_at: datetime | None = None
    assessment: SignalImpactAssessment | None = None


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


class ContinuousSensingArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    project_id: str
    watch_terms: list[str]
    feed_urls: list[str] = Field(default_factory=list)
    signals: list[SensingSignal] = Field(default_factory=list)
    review_tasks: list[SensingImpactReviewTask] = Field(default_factory=list)
    fetch_errors: list[str] = Field(default_factory=list)
    refreshed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
