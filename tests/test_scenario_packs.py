from __future__ import annotations

import pytest

from src.core.registry import ExtensionRegistry
from src.knowledge.sop import load_active_sop
from src.scenarios import builtin_scenario_packs
from src.scenarios import ScenarioInputError, ScenarioWorkflowRunner
from src.services.research_planning import ResearchPlanningService, SOPComplianceError
from src.services.company_assessment import CompanyAssessmentService
from src.state.project import ProjectState
from src.api.app import capabilities


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
        "growth_strategy",
        "pe",
        "vc",
        "sme_growth",
        "pe_vc",
    }
    assert "投资" in registry.get("pe_vc", "1.0.0").research_instructions()["decision_lens"]
    assert "target_company" in registry.get("sme_growth", "1.0.0").required_inputs()["required"]
    assert registry.get("sme_growth", "1.0.0").manifest().deprecated
    assert registry.get("pe_vc", "1.0.0").manifest().deprecated


def test_pe_and_vc_are_distinct_executable_scenario_contracts() -> None:
    registry = ExtensionRegistry(builtin_scenario_packs())
    pe = registry.get("pe", "1.0.0")
    vc = registry.get("vc", "1.0.0")

    assert pe.report_template()["type"] == "pe_ic_memo"
    assert vc.report_template()["type"] == "vc_ic_memo"
    assert "pe_diligence" in {node.node_id for node in pe.workflow()}
    assert "vc_diligence" in {node.node_id for node in vc.workflow()}
    assert pe.interview_policy()["goal"] != vc.interview_policy()["goal"]
    assert pe.evidence_policy()["independent_market_sizing"] is True
    assert vc.evidence_policy()["independent_market_sizing"] is True
    assert pe.feedback_policy()["subject"] == "pe_value_creation_plan"
    assert vc.feedback_policy()["subject"] == "vc_portfolio_milestones"
    assert pe.feedback_policy()["approval_role"] != vc.feedback_policy()["approval_role"]
    assert pe.decision_output_policy()["scorecard"]["enabled"] is False
    assert vc.decision_output_policy()["scorecard"]["opportunity_unit"] == "investment_hypothesis"


def test_growth_scorecard_and_action_plan_are_scenario_bound_and_skill_extensible() -> None:
    growth = ExtensionRegistry(builtin_scenario_packs()).get("growth_strategy", "1.0.0")
    policy = growth.decision_output_policy()

    assert "product_scenario_fit" in policy["scorecard"]["dimensions"]
    assert len(policy["action_plan"]["growth_tracks"]) == 2
    assert "1至2条" in policy["action_plan"]["portfolio_rule"]
    assert policy["strategy_skill_slot"]["slot_id"] == "growth_strategy_method"
    assert "evidence_traceability" in policy["strategy_skill_slot"]["protected_invariants"]

    service = CompanyAssessmentService(_UnusedModel(), load_active_sop(), ExtensionRegistry(builtin_scenario_packs()))
    specs = service._dimension_specs(_project(
        scenario_pack="growth_strategy",
        scenario_pack_version="1.0.0",
        company_strategy_objective="寻找第二增长曲线",
    ))
    assert set(specs) == set(policy["scorecard"]["dimensions"])
    assert round(sum(weight for _, weight in specs.values()), 6) == 1


def test_commercial_scenarios_embed_feedback_and_knowledge_writeback() -> None:
    registry = ExtensionRegistry(builtin_scenario_packs())

    growth = registry.get("growth_strategy", "1.0.0")
    pe = registry.get("pe", "1.0.0")
    vc = registry.get("vc", "1.0.0")

    assert [node.node_id for node in growth.workflow()][-3:] == [
        "action_feedback", "adaptive_plan", "knowledge_writeback"
    ]
    assert [node.node_id for node in pe.workflow()][-3:] == [
        "portfolio_feedback", "adaptive_plan", "knowledge_writeback"
    ]
    assert [node.node_id for node in vc.workflow()][-3:] == [
        "portfolio_feedback", "adaptive_investment_view", "knowledge_writeback"
    ]
    for pack in (growth, pe, vc):
        assert pack.feedback_policy()["enabled"] is True
        assert pack.feedback_policy()["deviation_classes"] == [
            "decision_assumption", "action_design", "execution_quality", "external_change"
        ]


def test_general_research_does_not_force_action_feedback_loop() -> None:
    general = ExtensionRegistry(builtin_scenario_packs()).get("general", "1.0.0")

    assert general.feedback_policy() == {"enabled": False}
    assert "knowledge_writeback" not in {node.node_id for node in general.workflow()}


def test_generic_runner_preserves_the_general_research_core_order() -> None:
    registry = ExtensionRegistry(builtin_scenario_packs())
    runner = ScenarioWorkflowRunner(registry)

    plan = runner.plan(
        "general",
        "1.0.0",
        {
            "industry": "工业机器人",
            "region": "全球",
            "research_objective": "判断竞争格局",
            "time_horizon": "2026-2030",
        },
    )

    assert [node.node_id for node in plan.nodes] == [
        "prompt_analysis",
        "scope",
        "research_plan",
        "web_research",
        "evidence_review",
        "industry_analysis",
        "future_intelligence",
        "content_review",
        "general_report",
    ]
    assert [node.review_gate for node in plan.nodes if node.review_gate] == [
        "gate_0",
        "gate_1",
        "gate_2",
    ]


def test_generic_runner_validates_scenario_inputs_before_execution() -> None:
    registry = ExtensionRegistry(builtin_scenario_packs())

    with pytest.raises(ScenarioInputError, match="target_company"):
        ScenarioWorkflowRunner(registry).plan(
            "pe",
            "1.0.0",
            {
                "industry": "IVD",
                "region": "中国",
                "research_objective": "评估标的",
                "time_horizon": "2026-2030",
            },
        )


def test_capability_catalog_is_available_without_initializing_model_providers() -> None:
    payload = capabilities()
    visible = {
        item["manifest"]["scenario_id"]
        for item in payload["scenario_contracts"]
        if not item["manifest"]["deprecated"]
    }

    assert visible == {"general", "growth_strategy", "pe", "vc"}


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
