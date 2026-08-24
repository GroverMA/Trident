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


class SignalImpactAssessment(BaseModel):
    affected_assets: list[str] = Field(default_factory=list)
    affected_hypotheses: list[str] = Field(default_factory=list)
    recommended_review: str
    confidence: int = Field(ge=0, le=100)


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


class ContinuousSensingArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    project_id: str
    watch_terms: list[str]
    feed_urls: list[str] = Field(default_factory=list)
    signals: list[SensingSignal] = Field(default_factory=list)
    fetch_errors: list[str] = Field(default_factory=list)
    refreshed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
