"""Evidence-linked industry analysis artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from src.models.research import MethodologyTrace


class AnalysisFindingType(StrEnum):
    FACT_SYNTHESIS = "fact_synthesis"
    SOURCE_VIEWPOINT = "source_viewpoint"
    ANALYST_INFERENCE = "analyst_inference"
    COMMERCIAL_JUDGMENT = "commercial_judgment"


class AnalysisReviewStatus(StrEnum):
    NEEDS_REVIEW = "needs_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FactorRole(StrEnum):
    DRIVER = "driver"
    CONSTRAINT = "constraint"
    ENABLING_CONDITION = "enabling_condition"
    MIXED = "mixed"
    CONDITIONAL = "conditional"


class ImpactDirection(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    UNCERTAIN = "uncertain"


class AnalysisFinding(BaseModel):
    finding_id: str = Field(default_factory=lambda: f"FND-{uuid4().hex[:10]}")
    subject: str
    finding_type: AnalysisFindingType
    statement: str
    mechanism: str
    evidence_ids: list[str] = Field(min_length=1)
    counter_evidence_ids: list[str] = Field(default_factory=list)
    comparison_dimensions: dict[str, str] = Field(default_factory=dict)
    factor_role: FactorRole | None = None
    impact_direction: ImpactDirection | None = None
    confidence: float = Field(ge=0, le=1)
    scope: str
    uncertainty: str
    boundary_condition: str
    review_status: AnalysisReviewStatus = AnalysisReviewStatus.NEEDS_REVIEW
    reviewer_note: str | None = None
    reviewed_at: datetime | None = None

    @field_validator("factor_role", "impact_direction", mode="before")
    @classmethod
    def normalize_optional_enum_nulls(cls, value: object) -> object:
        """Accept common model representations of an optional JSON null."""

        if isinstance(value, str) and value.strip().lower() in {
            "",
            "null",
            "none",
            "n/a",
            "na",
            "not_applicable",
            "不适用",
            "无",
        }:
            return None
        return value


class MarketSizingInput(BaseModel):
    name: str
    value: float = Field(gt=0)
    unit: str
    year: int
    evidence_id: str | None = None
    input_type: str = "observed"
    rationale: str


class MarketSizingEstimate(BaseModel):
    scope: str
    currency: str
    unit: str
    price_basis: str
    base_year: int
    base_size: float = Field(gt=0)
    low_size: float = Field(gt=0)
    high_size: float = Field(gt=0)
    forecast_year: int
    forecast_size: float = Field(gt=0)
    forecast_cagr: float
    primary_method: str
    validation_method: str
    primary_equation: str
    validation_equation: str
    inputs: list[MarketSizingInput] = Field(min_length=2)
    reconciliation: str
    sensitivities: list[str] = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    analyst_estimate: bool = True


class IndustryAnalysisModule(BaseModel):
    module_id: str
    title: str
    executive_summary: str
    findings: list[AnalysisFinding] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    rejected_questions: list[str] = Field(default_factory=list)
    market_sizing: MarketSizingEstimate | None = None


class IndustryAnalysisArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: uuid4().hex)
    evidence_collection_id: str
    input_evidence_ids: list[str] = Field(min_length=1)
    modules: list[IndustryAnalysisModule] = Field(min_length=5, max_length=5)
    company_implications: list[AnalysisFinding] = Field(default_factory=list)
    cross_module_conflicts: list[str] = Field(default_factory=list)
    overall_evidence_limitations: list[str] = Field(default_factory=list)
    methodology: MethodologyTrace
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    human_confirmed: bool = False

    @property
    def findings(self) -> list[AnalysisFinding]:
        return [
            finding
            for module in self.modules
            for finding in module.findings
        ] + list(self.company_implications)
