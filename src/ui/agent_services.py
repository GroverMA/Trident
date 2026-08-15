"""Construct UI-facing agent services from secure runtime configuration."""

from __future__ import annotations

import streamlit as st

from src.core.container import ServiceContainer
from src.services.evidence_collection import EvidenceCollectionService
from src.services.action_planning import ActionPlanningService
from src.services.company_assessment import CompanyAssessmentService
from src.services.future_intelligence import FutureIntelligenceService
from src.services.industry_analysis import IndustryAnalysisService
from src.services.research_planning import ResearchPlanningService
from src.services.report_generation import ReportGenerationService
from src.services.reviewer_orchestration import ReviewerOrchestrationService
from src.services.reviewer_revision import ReviewerRevisionService


def research_planning_service() -> ResearchPlanningService:
    return _service_container().research_planning


SERVICE_CONTAINER_CACHE_VERSION = "research-core-foundation-v1"


@st.cache_resource(show_spinner=False)
def _cached_service_container(cache_version: str) -> ServiceContainer:
    """Keep one framework-neutral service graph for the active app process."""

    del cache_version
    return ServiceContainer.from_runtime()


def _service_container() -> ServiceContainer:
    return _cached_service_container(SERVICE_CONTAINER_CACHE_VERSION)


def evidence_collection_service() -> EvidenceCollectionService:
    """Return a versioned service so Streamlit never reuses pre-hotfix code."""

    return _service_container().evidence_collection


def industry_analysis_service() -> IndustryAnalysisService:
    return _service_container().industry_analysis


def future_intelligence_service() -> FutureIntelligenceService:
    return _service_container().future_intelligence


def report_generation_service() -> ReportGenerationService:
    return _service_container().report_generation


def company_assessment_service() -> CompanyAssessmentService:
    return _service_container().company_assessment


def action_planning_service() -> ActionPlanningService:
    return _service_container().action_planning


def reviewer_orchestration_service() -> ReviewerOrchestrationService:
    """Build the report-first Reviewer pipeline from the same production services.

    The orchestration layer uses temporary approved copies only while satisfying
    downstream service contracts.  Returned artifacts remain pending review.
    """

    return _service_container().reviewer_orchestration


def reviewer_revision_service() -> ReviewerRevisionService:
    return _service_container().reviewer_revision
