from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.config import Settings
from src.core.contracts import ExtensionDescriptor
from src.core.container import ServiceContainer
from src.core.registry import ExtensionRegistrationError, ExtensionRegistry
from src.core.runtime import CandidateStage, EvolutionPolicy, ResearchRunContext
from src.knowledge.sop import load_active_sop


@dataclass
class FakePack:
    descriptor: ExtensionDescriptor

    def research_instructions(self):
        return {"workflow": "test"}

    def required_inputs(self):
        return {}


class FakeModel:
    def list_models(self):
        return ["fake"]

    def complete(self, *args, **kwargs):
        del args, kwargs
        return {}


class FakeSearchRouter:
    pass


def _settings() -> Settings:
    return Settings(
        model_api_key="test",
        model_base_url="https://model.invalid",
        model_name="fake",
        agenthub_endpoint="https://search.invalid/agent",
        search_mcp_url="https://search.invalid/mcp",
        app_name="test",
        app_key="test",
    )


def test_extension_registry_keeps_versions_independent():
    registry = ExtensionRegistry()
    v1 = FakePack(ExtensionDescriptor("pe-vc", "1.0", "PE/VC"))
    v2 = FakePack(ExtensionDescriptor("pe-vc", "2.0", "PE/VC"))

    registry.register(v1)
    registry.register(v2)

    assert registry.get("pe-vc", "1.0") is v1
    assert registry.versions("pe-vc") == ("1.0", "2.0")
    with pytest.raises(ExtensionRegistrationError):
        registry.register(v1)


def test_evolution_policy_blocks_unreviewed_or_weak_candidates():
    policy = EvolutionPolicy(minimum_eval_score=0.85, minimum_eval_cases=50)

    assert not policy.may_enter_canary(
        stage=CandidateStage.OFFLINE_VALIDATED,
        eval_score=0.90,
        eval_cases=80,
        human_approved=False,
    )
    assert not policy.may_enter_canary(
        stage=CandidateStage.HUMAN_APPROVED,
        eval_score=0.70,
        eval_cases=80,
        human_approved=True,
    )
    assert policy.may_enter_canary(
        stage=CandidateStage.HUMAN_APPROVED,
        eval_score=0.90,
        eval_cases=80,
        human_approved=True,
    )


def test_run_context_pins_workflow_and_pack_versions():
    context = ResearchRunContext(
        project_id="project-1",
        workflow_version="2",
        scenario_id="growth",
        scenario_version="3",
        industry_pack_id="ivd",
        industry_pack_version="1",
    )

    assert context.run_id
    assert context.scenario_id == "growth"
    assert context.industry_pack_version == "1"


def test_container_reuses_one_service_graph_without_streamlit():
    container = ServiceContainer(
        settings=_settings(),
        sop=load_active_sop(),
        model_factory=lambda settings: FakeModel(),
        search_factory=lambda settings: FakeSearchRouter(),
    )

    assert container.research_planning is container.research_planning
    assert container.evidence_collection is container.evidence_collection
    assert container.reviewer_orchestration.planning is container.research_planning
    assert container.reviewer_orchestration.evidence is container.evidence_collection
