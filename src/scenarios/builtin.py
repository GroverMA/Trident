"""Versioned executable scenario packs built on one Research Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from src.core.contracts import ExtensionDescriptor, ScenarioManifest, ScenarioWorkflowNode


RESEARCH_CORE_NODES = (
    ScenarioWorkflowNode("prompt_analysis", "research.prompt_analysis"),
    ScenarioWorkflowNode("scope", "research.scope", ("prompt_analysis",), "gate_0"),
    ScenarioWorkflowNode("research_plan", "research.plan", ("scope",)),
    ScenarioWorkflowNode("web_research", "research.evidence", ("research_plan",)),
    ScenarioWorkflowNode("evidence_review", "research.evidence_review", ("web_research",), "gate_1"),
    ScenarioWorkflowNode("industry_analysis", "research.industry_analysis", ("evidence_review",)),
    ScenarioWorkflowNode("future_intelligence", "research.future_intelligence", ("industry_analysis",)),
    ScenarioWorkflowNode("content_review", "research.content_review", ("future_intelligence",), "gate_2"),
)


def research_core_after(node_id: str) -> tuple[ScenarioWorkflowNode, ...]:
    """Reuse the exact core while attaching its first node to a scenario prelude."""

    first, *rest = RESEARCH_CORE_NODES
    return (
        ScenarioWorkflowNode(
            first.node_id,
            first.capability,
            (node_id,),
            first.review_gate,
            first.checkpoint,
        ),
        *rest,
    )


@dataclass(frozen=True, slots=True)
class BuiltinScenarioPack:
    descriptor: ExtensionDescriptor
    instructions: Mapping[str, Any]
    inputs: Mapping[str, Any]
    workflow_nodes: tuple[ScenarioWorkflowNode, ...]
    interview: Mapping[str, Any] = field(default_factory=dict)
    evidence: Mapping[str, Any] = field(default_factory=dict)
    gates: Mapping[str, Any] = field(default_factory=dict)
    outputs: Mapping[str, Any] = field(default_factory=dict)
    rubric: Mapping[str, Any] = field(default_factory=dict)
    report: Mapping[str, Any] = field(default_factory=dict)
    ui: Mapping[str, Any] = field(default_factory=dict)
    feedback: Mapping[str, Any] = field(default_factory=dict)
    deprecated: bool = False
    replaces: tuple[str, ...] = ()

    def manifest(self) -> ScenarioManifest:
        return ScenarioManifest(
            scenario_id=self.descriptor.extension_id,
            version=self.descriptor.version,
            deprecated=self.deprecated,
            replaces=self.replaces,
        )

    def research_instructions(self) -> Mapping[str, Any]:
        return self.instructions

    def required_inputs(self) -> Mapping[str, Any]:
        return self.inputs

    def workflow(self) -> tuple[ScenarioWorkflowNode, ...]:
        return self.workflow_nodes

    def interview_policy(self) -> Mapping[str, Any]:
        return self.interview

    def evidence_policy(self) -> Mapping[str, Any]:
        return self.evidence

    def review_gates(self) -> Mapping[str, Any]:
        return self.gates

    def output_schema(self) -> Mapping[str, Any]:
        return self.outputs

    def evaluation_rubric(self) -> Mapping[str, Any]:
        return self.rubric

    def report_template(self) -> Mapping[str, Any]:
        return self.report

    def ui_schema(self) -> Mapping[str, Any]:
        return self.ui

    def feedback_policy(self) -> Mapping[str, Any]:
        return self.feedback


def _pack(
    *,
    scenario_id: str,
    name: str,
    description: str,
    capabilities: tuple[str, ...],
    lens: str,
    required_outputs: list[str],
    required_inputs: list[str],
    workflow: tuple[ScenarioWorkflowNode, ...],
    interview_goal: str,
    starter_questions: list[str],
    upload_guides: list[str],
    card_flow: str,
    route: str,
    report_type: str,
    diagnostic_topics: list[str] | None = None,
    feedback_policy: Mapping[str, Any] | None = None,
    deprecated: bool = False,
    replaces: tuple[str, ...] = (),
) -> BuiltinScenarioPack:
    evidence_policy = {
        "research_skills_locked": True,
        "independent_market_sizing": True,
        "secondary_source_cross_check": True,
        "human_acceptance_required": True,
    }
    return BuiltinScenarioPack(
        descriptor=ExtensionDescriptor(
            extension_id=scenario_id,
            version="1.0.0",
            display_name=name,
            description=description,
            capabilities=capabilities,
        ),
        instructions={"decision_lens": lens, "required_outputs": required_outputs},
        inputs={"required": required_inputs},
        workflow_nodes=workflow,
        interview={
            "mode": "adaptive",
            "goal": interview_goal,
            "starter_questions": starter_questions,
            "diagnostic_topics": diagnostic_topics or [],
            "suggested_uploads": upload_guides,
            "user_confirmation_required": True,
        },
        evidence=evidence_policy,
        gates={"gate_0": "confirm_scope", "gate_1": "confirm_evidence", "gate_2": "confirm_content"},
        outputs={"required": required_outputs},
        rubric={
            "evidence_traceability": 0.30,
            "decision_usefulness": 0.30,
            "method_compliance": 0.25,
            "uncertainty_disclosure": 0.15,
        },
        report={"type": report_type, "standalone_reader": True},
        ui={
            "entry": "scenario_workspace",
            "route": route,
            "card_flow": card_flow,
            "upload_guides": upload_guides,
            "show_project_navigation": True,
            "review_layout": "compact_table",
        },
        feedback=feedback_policy or {"enabled": False},
        deprecated=deprecated,
        replaces=replaces,
    )


def builtin_scenario_packs() -> tuple[BuiltinScenarioPack, ...]:
    general = _pack(
        scenario_id="general",
        name="通用行业研究",
        description="完整行业定义、规模、竞争、驱动、趋势与报告流程。",
        capabilities=("industry-research", "evidence-review", "scenario-analysis"),
        lens="形成证据可追溯的行业判断，不虚构企业决策背景。",
        required_outputs=["行业边界", "市场规模", "竞争格局", "驱动因素", "未来情景"],
        required_inputs=["industry", "region", "research_objective", "time_horizon"],
        workflow=RESEARCH_CORE_NODES + (
            ScenarioWorkflowNode("general_report", "research.general_report", ("content_review",)),
        ),
        interview_goal="澄清研究问题、边界、口径与必须回答的问题",
        starter_questions=[],
        upload_guides=[],
        card_flow="定义问题 → 研究路径 → 完整报告",
        route="/research",
        report_type="general_report",
        feedback_policy={"enabled": False},
    )
    growth = _pack(
        scenario_id="growth_strategy",
        name="企业增长决策",
        description="把企业诊断与行业证据映射为增长选择、能力差距和行动计划。",
        capabilities=("growth-strategy", "company-scorecard", "action-plan"),
        lens="围绕企业真实增长问题研究，区分市场事实、企业事实与待验证陈述。",
        required_outputs=["企业画像", "机会地图", "能力差距", "Company Scorecard", "Action Plan"],
        required_inputs=["industry", "region", "research_objective", "time_horizon", "target_company", "company_strategy_objective"],
        workflow=(
            ScenarioWorkflowNode("diagnostic_interview", "consulting.interview"),
            ScenarioWorkflowNode("enterprise_profile", "portfolio.enterprise_profile", ("diagnostic_interview",), "profile_gate"),
        ) + research_core_after("enterprise_profile") + (
            ScenarioWorkflowNode("company_scorecard", "strategy.company_scorecard", ("content_review",)),
            ScenarioWorkflowNode("action_plan", "strategy.action_plan", ("company_scorecard",), "action_gate"),
            ScenarioWorkflowNode("action_feedback", "feedback.action_progress", ("action_plan",)),
            ScenarioWorkflowNode("adaptive_plan", "feedback.plan_revision", ("action_feedback",), "plan_revision_gate"),
            ScenarioWorkflowNode("knowledge_writeback", "memory.enterprise_writeback", ("adaptive_plan",)),
        ),
        interview_goal="形成企业、管理层决策风格、增长目标、资源与数据缺口画像",
        starter_questions=[
            "过去12个月，收入或利润最明显的变化是什么？你认为主要原因是什么？",
            "目前最依赖哪类客户、产品或渠道？如果它停止增长，影响会有多大？",
            "管理层遇到重大分歧时通常怎样做决定？",
            "为了实现这次增长目标，公司目前最缺少什么？",
        ],
        diagnostic_topics=["performance_change", "concentration_risk", "decision_style", "capability_gap"],
        upload_guides=["销售业绩与订单", "财务报表", "客户与渠道情况", "产品与区域毛利", "组织与战略资料"],
        card_flow="主动诊断 → 机会研究 → 战略 → 行动",
        route="/enterprise",
        report_type="growth_decision_report",
        feedback_policy={
            "enabled": True,
            "subject": "enterprise_action_plan",
            "feedback_fields": ["progress_pct", "outcome_metrics", "customer_feedback", "blockers", "owner_comment", "evidence_refs"],
            "deviation_classes": ["decision_assumption", "action_design", "execution_quality", "external_change"],
            "approval_role": "enterprise_management",
            "dashboard_dimensions": ["decision_quality", "action_quality", "execution_quality", "customer_market_quality", "learning_quality"],
        },
        replaces=("sme_growth@1.0.0",),
    )
    pe = _pack(
        scenario_id="pe",
        name="PE 投资分析",
        description="成熟企业经营质量、交易边界、价值创造、下行情景与退出研究。",
        capabilities=("buyout-thesis", "commercial-dd", "value-creation", "ic-memo"),
        lens="围绕控制权、现金流、杠杆、持有期、价值创造和退出验证投资假设。",
        required_outputs=["标的画像", "投资假设", "价值创造计划", "下行情景", "退出路径", "IC Memo"],
        required_inputs=["industry", "region", "research_objective", "time_horizon", "target_company"],
        workflow=(
            ScenarioWorkflowNode("investment_interview", "consulting.interview"),
            ScenarioWorkflowNode("target_profile", "portfolio.target_profile", ("investment_interview",), "profile_gate"),
        ) + research_core_after("target_profile") + (
            ScenarioWorkflowNode("pe_diligence", "investment.pe_diligence", ("content_review",)),
            ScenarioWorkflowNode("ic_memo", "investment.ic_memo", ("pe_diligence",), "ic_gate"),
            ScenarioWorkflowNode("value_creation_plan", "investment.value_creation_plan", ("ic_memo",)),
            ScenarioWorkflowNode("portfolio_feedback", "feedback.portfolio_progress", ("value_creation_plan",)),
            ScenarioWorkflowNode("adaptive_plan", "feedback.plan_revision", ("portfolio_feedback",), "plan_revision_gate"),
            ScenarioWorkflowNode("knowledge_writeback", "memory.target_writeback", ("adaptive_plan",)),
        ),
        interview_goal="校准投资策略、回报边界、交易约束和需要验证的价值创造假设",
        starter_questions=[
            "你在这类交易中更偏好经营改善、行业整合，还是稳定现金流？",
            "什么情况会让你直接放弃一个标的？",
            "对持有期、目标回报和杠杆水平，你通常采用怎样的边界？",
            "这次标的最需要验证的投资假设是什么？",
        ],
        diagnostic_topics=["investment_thesis", "target_quality", "value_creation", "deal_boundary"],
        upload_guides=["财务三表与经营数据", "客户与合同", "管理层资料", "股权与交易结构", "商业计划与预算"],
        card_flow="投资风格 → 标的诊断 → DD → IC Memo",
        route="/?scenario=pe",
        report_type="pe_ic_memo",
        feedback_policy={
            "enabled": True,
            "subject": "pe_value_creation_plan",
            "feedback_fields": ["progress_pct", "outcome_metrics", "management_feedback", "customer_feedback", "blockers", "evidence_refs"],
            "deviation_classes": ["decision_assumption", "action_design", "execution_quality", "external_change"],
            "approval_role": "investment_committee_or_board",
            "dashboard_dimensions": ["decision_quality", "action_quality", "execution_quality", "operating_customer_quality", "learning_quality"],
        },
        replaces=("pe_vc@1.0.0",),
    )
    vc = _pack(
        scenario_id="vc",
        name="VC 投资分析",
        description="机会发现、团队、技术、市场时点、里程碑和后续融资研究。",
        capabilities=("venture-screening", "founder-tech-dd", "milestone-planning", "ic-memo"),
        lens="围绕团队、技术、市场时点、增长上限、关键里程碑和跟投逻辑验证投资机会。",
        required_outputs=["公司快照", "市场时点", "团队与技术验证", "关键里程碑", "融资逻辑", "IC Memo"],
        required_inputs=["industry", "region", "research_objective", "time_horizon", "target_company"],
        workflow=(
            ScenarioWorkflowNode("investment_interview", "consulting.interview"),
            ScenarioWorkflowNode("target_profile", "portfolio.target_profile", ("investment_interview",), "profile_gate"),
        ) + research_core_after("target_profile") + (
            ScenarioWorkflowNode("vc_diligence", "investment.vc_diligence", ("content_review",)),
            ScenarioWorkflowNode("ic_memo", "investment.ic_memo", ("vc_diligence",), "ic_gate"),
            ScenarioWorkflowNode("milestone_plan", "investment.milestone_plan", ("ic_memo",)),
            ScenarioWorkflowNode("portfolio_feedback", "feedback.portfolio_progress", ("milestone_plan",)),
            ScenarioWorkflowNode("adaptive_investment_view", "feedback.investment_revision", ("portfolio_feedback",), "plan_revision_gate"),
            ScenarioWorkflowNode("knowledge_writeback", "memory.target_writeback", ("adaptive_investment_view",)),
        ),
        interview_goal="识别投资偏好、淘汰标准、风险承受方式和标的关键待验证问题",
        starter_questions=[
            "你的基金当前重点关注哪些赛道、轮次和地域？",
            "在团队、技术、市场和商业化之间，你最先淘汰项目的标准是什么？",
            "你更愿意为巨大市场中的早期产品，还是小市场中的明确领先者承担风险？",
            "关于这个标的，目前最让你犹豫的一项信息是什么？",
        ],
        diagnostic_topics=["investment_style", "founder_team", "market_timing", "milestone_risk"],
        upload_guides=["BP / Teaser", "产品与技术资料", "团队介绍", "融资历史与Cap Table", "已有客户或验证数据"],
        card_flow="决策风格 → 初筛 → DD → 投后跟踪",
        route="/?scenario=vc",
        report_type="vc_ic_memo",
        feedback_policy={
            "enabled": True,
            "subject": "vc_portfolio_milestones",
            "feedback_fields": ["progress_pct", "milestone_metrics", "founder_feedback", "customer_feedback", "runway", "blockers", "evidence_refs"],
            "deviation_classes": ["decision_assumption", "action_design", "execution_quality", "external_change"],
            "approval_role": "fund_authorized_reviewer",
            "dashboard_dimensions": ["decision_quality", "support_action_quality", "execution_quality", "customer_market_quality", "learning_quality"],
        },
        replaces=("pe_vc@1.0.0",),
    )
    legacy_growth = _pack(
        scenario_id="sme_growth",
        name="企业增长决策（兼容）",
        description="历史项目兼容入口；新项目迁移至 growth_strategy。",
        capabilities=growth.descriptor.capabilities,
        lens=str(growth.instructions["decision_lens"]),
        required_outputs=list(growth.outputs["required"]),
        required_inputs=list(growth.inputs["required"]),
        workflow=growth.workflow_nodes,
        interview_goal=str(growth.interview["goal"]),
        starter_questions=list(growth.interview["starter_questions"]),
        upload_guides=list(growth.ui["upload_guides"]),
        card_flow=str(growth.ui["card_flow"]),
        route="/enterprise",
        report_type="growth_decision_report",
        feedback_policy=growth.feedback_policy(),
        deprecated=True,
    )
    legacy_pe_vc = _pack(
        scenario_id="pe_vc",
        name="PE/VC 赛道研判（兼容）",
        description="历史项目兼容入口；新项目必须选择 PE 或 VC。",
        capabilities=("investment-thesis", "target-landscape", "risk-diligence"),
        lens="服务投资筛选而非无条件投资建议；明确投资假设、反证和待尽调事项。",
        required_outputs=["赛道吸引力", "价值池", "标的地图", "投资假设", "主要风险", "尽调问题"],
        required_inputs=["industry", "region", "research_objective", "time_horizon"],
        workflow=RESEARCH_CORE_NODES,
        interview_goal="保留历史项目上下文",
        starter_questions=[],
        upload_guides=[],
        card_flow="历史兼容",
        route="/research",
        report_type="legacy_investment_report",
        feedback_policy={"enabled": False},
        deprecated=True,
    )
    return general, growth, pe, vc, legacy_growth, legacy_pe_vc
