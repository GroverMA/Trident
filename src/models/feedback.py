"""Versioned execution feedback shared by scenario packs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class ActionFeedbackEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: f"FDB-{uuid4().hex[:10]}")
    action_id: str
    progress_pct: int = Field(ge=0, le=100)
    outcome_metrics: str = ""
    blockers: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    scenario_fields: dict[str, str] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("action_id")
    @classmethod
    def require_action(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("action_id is required")
        return cleaned


class ActionFeedbackArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"AFB-{uuid4().hex[:10]}")
    project_id: str
    scenario_id: str
    action_plan_id: str
    entries: list[ActionFeedbackEntry] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FeedbackDashboard(BaseModel):
    action_count: int
    actions_with_feedback: int
    coverage_pct: int = Field(ge=0, le=100)
    average_progress_pct: int = Field(ge=0, le=100)
    blocker_count: int = Field(ge=0)
    adjustment_required: bool
    last_feedback_at: datetime | None = None


class DeviationClass(StrEnum):
    DECISION_ASSUMPTION = "decision_assumption"
    ACTION_DESIGN = "action_design"
    EXECUTION_QUALITY = "execution_quality"
    EXTERNAL_CHANGE = "external_change"


class ProposalReviewStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ActionAdjustmentProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"ADJ-{uuid4().hex[:10]}")
    action_id: str
    feedback_entry_ids: list[str] = Field(min_length=1)
    deviation_class: DeviationClass
    diagnosis: str
    recommendation: str
    proposed_rationale: str
    proposed_timing: str | None = None
    confidence: int = Field(ge=0, le=100)
    review_status: ProposalReviewStatus = ProposalReviewStatus.NEEDS_REVIEW
    reviewer_note: str | None = None
    reviewed_at: datetime | None = None


class PlanRevisionArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"PRV-{uuid4().hex[:10]}")
    project_id: str
    scenario_id: str
    base_action_plan_id: str
    feedback_artifact_id: str
    proposals: list[ActionAdjustmentProposal] = Field(min_length=1)
    summary: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    human_confirmed: bool = False
    confirmed_at: datetime | None = None


class EnterpriseTimelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"TML-{uuid4().hex[:10]}")
    event_type: str
    project_id: str
    scenario_id: str
    title: str
    summary: str
    artifact_ids: list[str] = Field(default_factory=list)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
