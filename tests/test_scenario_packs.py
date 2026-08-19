from __future__ import annotations

import pytest

from src.core.registry import ExtensionRegistry
from src.knowledge.sop import load_active_sop
from src.scenarios import builtin_scenario_packs
from src.services.research_planning import ResearchPlanningService, SOPComplianceError
from src.state.project import ProjectState


class _UnusedModel:
    pass


def _project(**updates) -> ProjectState:
    values = {
        "project_name": "测试项目",
        "industry": "工业机器人",
        "region": "中国",
        "research_objective": "判断未来增长机会",
        "time_horizon": "2026-2030",
    }
    values.update(updates)
    return ProjectState(**values)


def test_builtin_scenario_packs_have_stable_versions_and_distinct_lenses() -> None:
    registry = ExtensionRegistry(builtin_scenario_packs())

    assert {item.extension_id for item in registry.descriptors()} == {
        "general",
        "sme_growth",
        "pe_vc",
    }
    assert "投资" in registry.get("pe_vc", "1.0.0").research_instructions()["decision_lens"]
    assert "target_company" in registry.get("sme_growth", "1.0.0").required_inputs()["required"]


def test_planning_resolves_selected_scenario_context() -> None:
    registry = ExtensionRegistry(builtin_scenario_packs())
    service = ResearchPlanningService(_UnusedModel(), load_active_sop(), registry)

    context = service._scenario_context(_project(scenario_pack="pe_vc"))

    assert context["scenario_pack"]["id"] == "pe_vc"
    assert "尽调问题" in context["scenario_pack"]["instructions"]["required_outputs"]


def test_unknown_scenario_pack_is_rejected_before_model_call() -> None:
    service = ResearchPlanningService(
        _UnusedModel(), load_active_sop(), ExtensionRegistry(builtin_scenario_packs())
    )

    with pytest.raises(SOPComplianceError, match="未知场景包"):
        service._scenario_context(_project(scenario_pack="missing"))
