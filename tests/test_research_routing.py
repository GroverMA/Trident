from src.core.registry import ExtensionRegistry
from src.models.interview import EntityProfileArtifact
from src.scenarios import builtin_scenario_packs
from src.services.research_routing import ScenarioResearchRouter
from src.state.project import ProjectState, ResearchPath


def project_for(scenario: str) -> ProjectState:
    return ProjectState(
        project_name=f"{scenario} route",
        industry="工业机器人",
        region="中国",
        research_objective="选择研究通路",
        time_horizon="未来3年",
        target_company="示例企业",
        company_strategy_enabled=scenario == "growth_strategy",
        company_strategy_objective="寻找增长机会" if scenario == "growth_strategy" else None,
        scenario_pack=scenario,
        scenario_pack_version="1.0.0",
        entity_profile_artifact=EntityProfileArtifact(
            scenario_id=scenario,
            entity_name="示例企业",
            objective="选择研究通路",
            operating_portrait="画像",
            decision_style="审慎",
            research_next_step="进入行业研究",
            human_confirmed=True,
        ),
    )


def test_growth_always_builds_external_industry_evidence() -> None:
    router = ScenarioResearchRouter(ExtensionRegistry(builtin_scenario_packs()))
    routed = router.route(
        project_for("growth_strategy"),
        available_materials=["财务.xlsx", "销售.csv", "行业报告.pdf"],
        has_existing_report=True,
    )
    assert routed.research_path == ResearchPath.BUILD_FIRST
    assert routed.research_route_artifact is not None
    assert routed.research_route_artifact.data_scope["subject_type"] == "operating_company"


def test_pe_reviews_materials_then_builds_evidence_gaps() -> None:
    router = ScenarioResearchRouter(ExtensionRegistry(builtin_scenario_packs()))
    routed = router.route(
        project_for("pe"),
        available_materials=["IM.pdf", "财务模型.xlsx"],
    )
    assert routed.research_path == ResearchPath.REVIEW_FIRST
    assert routed.research_route_artifact is not None
    assert routed.research_route_artifact.supplemental_gap_research is True
    assert routed.research_route_artifact.data_scope["private_memory_root"] == "fund_deal_workspace"


def test_pe_without_materials_and_typical_vc_use_build_first() -> None:
    router = ScenarioResearchRouter(ExtensionRegistry(builtin_scenario_packs()))
    pe = router.route(project_for("pe"), available_materials=[])
    vc = router.route(project_for("vc"), available_materials=["BP.pdf"])
    assert pe.research_path == ResearchPath.BUILD_FIRST
    assert vc.research_path == ResearchPath.BUILD_FIRST


def test_vc_can_review_when_due_diligence_materials_are_complete() -> None:
    router = ScenarioResearchRouter(ExtensionRegistry(builtin_scenario_packs()))
    routed = router.route(
        project_for("vc"),
        available_materials=["BP.pdf", "技术DD.pdf", "客户验证.xlsx"],
        has_existing_report=True,
    )
    assert routed.research_path == ResearchPath.REVIEW_FIRST
    assert routed.research_route_artifact is not None
    assert routed.research_route_artifact.data_scope["subject_type"] == "venture_target"
