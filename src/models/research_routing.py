"""Persisted decision for embedding the shared research core in a scenario."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

class ResearchRouteDecision(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    scenario_id: str
    primary_path: Literal["research_build_first", "report_review_first"]
    supplemental_gap_research: bool = True
    mode_label: str
    rationale: list[str] = Field(default_factory=list)
    available_materials: list[str] = Field(default_factory=list)
    data_scope: dict[str, object] = Field(default_factory=dict)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
