"""Run metadata and governed evolution policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class CandidateStage(StrEnum):
    DRAFT = "draft"
    OFFLINE_VALIDATED = "offline_validated"
    HUMAN_APPROVED = "human_approved"
    CANARY = "canary"
    PRODUCTION = "production"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ResearchRunContext:
    project_id: str
    workflow_id: str = "industry-research"
    workflow_version: str = "1"
    scenario_id: str = "general"
    scenario_version: str = "1"
    industry_pack_id: str | None = None
    industry_pack_version: str | None = None
    run_id: str = field(default_factory=lambda: uuid4().hex)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class EvolutionPolicy:
    """Prevents an AI component from silently rewriting production behavior."""

    minimum_eval_score: float = 0.80
    minimum_eval_cases: int = 30
    require_human_approval: bool = True

    def may_enter_canary(
        self,
        *,
        stage: CandidateStage,
        eval_score: float,
        eval_cases: int,
        human_approved: bool,
    ) -> bool:
        return (
            stage in {CandidateStage.OFFLINE_VALIDATED, CandidateStage.HUMAN_APPROVED}
            and eval_score >= self.minimum_eval_score
            and eval_cases >= self.minimum_eval_cases
            and (human_approved or not self.require_human_approval)
        )
