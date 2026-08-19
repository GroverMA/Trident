"""Framework-neutral composition root for all current research services."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Callable

from src.config import Settings
from src.core.contracts import EventSink, NullEventSink
from src.core.registry import ExtensionRegistry
from src.knowledge.sop import ResearchSOPPack, load_active_sop
from src.providers.base import ModelProvider
from src.providers.hkgai_mcp import HKGAIMCPProvider
from src.providers.hkgai_model import HKGAIModelProvider
from src.providers.hkgai_structured_rest import HKGAIStructuredRestProvider
from src.providers.search_router import SearchRouter
from src.scenarios import builtin_scenario_packs
from src.services.action_planning import ActionPlanningService
from src.services.company_assessment import CompanyAssessmentService
from src.services.evidence_collection import EvidenceCollectionService
from src.services.future_intelligence import FutureIntelligenceService
from src.services.industry_analysis import IndustryAnalysisService
from src.services.report_generation import ReportGenerationService
from src.services.research_planning import ResearchPlanningService
from src.services.reviewer_orchestration import ReviewerOrchestrationService
from src.services.reviewer_revision import ReviewerRevisionService


ModelFactory = Callable[[Settings], ModelProvider]
SearchFactory = Callable[[Settings], SearchRouter]


def _default_model_factory(settings: Settings) -> ModelProvider:
    return HKGAIModelProvider(settings)


def _default_search_factory(settings: Settings) -> SearchRouter:
    return SearchRouter(
        HKGAIMCPProvider(settings),
        HKGAIStructuredRestProvider(settings),
        mode=settings.search_transport,
    )


@dataclass
class ServiceContainer:
    """Creates one coherent service graph for UI, API or worker processes.

    Factories are injectable so tests and future algorithm teams can replace a
    provider without changing research services or delivery-channel code.
    """

    settings: Settings
    sop: ResearchSOPPack
    model_factory: ModelFactory = _default_model_factory
    search_factory: SearchFactory = _default_search_factory
    scenario_packs: ExtensionRegistry = field(
        default_factory=lambda: ExtensionRegistry(builtin_scenario_packs())
    )
    industry_packs: ExtensionRegistry = field(default_factory=ExtensionRegistry)
    algorithms: ExtensionRegistry = field(default_factory=ExtensionRegistry)
    evaluators: ExtensionRegistry = field(default_factory=ExtensionRegistry)
    event_sink: EventSink = field(default_factory=NullEventSink)

    @classmethod
    def from_runtime(cls) -> "ServiceContainer":
        return cls(settings=Settings.load(), sop=load_active_sop())

    def _model(self) -> ModelProvider:
        return self.model_factory(self.settings)

    @cached_property
    def research_planning(self) -> ResearchPlanningService:
        return ResearchPlanningService(
            model=self._model(), sop=self.sop, scenario_packs=self.scenario_packs
        )

    @cached_property
    def evidence_collection(self) -> EvidenceCollectionService:
        return EvidenceCollectionService(
            model=self._model(), search=self.search_factory(self.settings)
        )

    @cached_property
    def industry_analysis(self) -> IndustryAnalysisService:
        return IndustryAnalysisService(model=self._model(), sop=self.sop)

    @cached_property
    def future_intelligence(self) -> FutureIntelligenceService:
        return FutureIntelligenceService(model=self._model(), sop=self.sop)

    @cached_property
    def report_generation(self) -> ReportGenerationService:
        return ReportGenerationService(model=self._model())

    @cached_property
    def company_assessment(self) -> CompanyAssessmentService:
        return CompanyAssessmentService(model=self._model(), sop=self.sop)

    @cached_property
    def action_planning(self) -> ActionPlanningService:
        return ActionPlanningService(model=self._model(), sop=self.sop)

    @cached_property
    def reviewer_revision(self) -> ReviewerRevisionService:
        return ReviewerRevisionService(model=self._model())

    @cached_property
    def reviewer_orchestration(self) -> ReviewerOrchestrationService:
        return ReviewerOrchestrationService(
            planning=self.research_planning,
            evidence=self.evidence_collection,
            industry=self.industry_analysis,
            future=self.future_intelligence,
            report=self.report_generation,
            company=self.company_assessment,
            action=self.action_planning,
        )
