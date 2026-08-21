"""Persistent artifacts for scenario-native diagnostic interviews."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class InterviewStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    READY_FOR_PROFILE = "ready_for_profile"
    COMPLETED = "completed"


class InterviewAnswerAnalysis(BaseModel):
    """Auditable reasoning result for one user answer.

    Extracted facts remain separate from ambiguities and gaps so a spoken
    management opinion can never silently become a verified company fact.
    """

    summary: str = ""
    extracted_facts: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    answer_quality: str = "partial"
    topic_complete: bool = False
    follow_up_question: str | None = None
    confidence: float = Field(default=0.5, ge=0, le=1)


class InterviewTurn(BaseModel):
    turn_id: str = Field(default_factory=lambda: uuid4().hex)
    topic_id: str
    question: str
    answer: str | None = None
    answer_quality: str = "pending"
    analysis: InterviewAnswerAnalysis | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ScenarioInterviewArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    scenario_id: str
    scenario_version: str
    objective: str
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    turns: list[InterviewTurn] = Field(default_factory=list)
    covered_topics: list[str] = Field(default_factory=list)
    remaining_topics: list[str] = Field(default_factory=list)
    suggested_uploads: list[str] = Field(default_factory=list)
    analysis_mode: str = "adaptive"
    provider_warning: str | None = None
    max_turns: int = 12
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_turn(self) -> InterviewTurn | None:
        return next((turn for turn in reversed(self.turns) if turn.answer is None), None)


class EntityProfileArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    scenario_id: str
    entity_name: str
    objective: str
    operating_portrait: str
    decision_style: str
    research_next_step: str
    known_facts: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    source_turn_ids: list[str] = Field(default_factory=list)
    human_confirmed: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
