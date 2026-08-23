"""Versioned execution feedback shared by scenario packs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

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
