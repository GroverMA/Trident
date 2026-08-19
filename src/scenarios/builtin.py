"""Versioned scenario packs that specialise prompts without forking the agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.core.contracts import ExtensionDescriptor


@dataclass(frozen=True, slots=True)
class BuiltinScenarioPack:
    descriptor: ExtensionDescriptor
    instructions: Mapping[str, Any]
    inputs: Mapping[str, Any]

    def research_instructions(self) -> Mapping[str, Any]:
        return self.instructions

    def required_inputs(self) -> Mapping[str, Any]:
        return self.inputs


def builtin_scenario_packs() -> tuple[BuiltinScenarioPack, ...]:
    return (
        BuiltinScenarioPack(
            descriptor=ExtensionDescriptor(
                extension_id="general",
                version="1.0.0",
                display_name="通用行业研究",
                description="完整行业定义、规模、竞争、驱动、趋势与报告流程。",
                capabilities=("industry-research", "evidence-review", "scenario-analysis"),
            ),
            instructions={
                "decision_lens": "形成证据可追溯的行业判断，不虚构企业决策背景。",
                "required_outputs": ["行业边界", "市场规模", "竞争格局", "驱动因素", "未来情景"],
            },
            inputs={"required": ["industry", "region", "research_objective", "time_horizon"]},
        ),
        BuiltinScenarioPack(
            descriptor=ExtensionDescriptor(
                extension_id="sme_growth",
                version="1.0.0",
                display_name="企业增长决策",
                description="把行业证据映射到目标企业能力、增长选择和行动计划。",
                capabilities=("growth-strategy", "company-scorecard", "action-plan"),
            ),
            instructions={
                "decision_lens": "围绕目标企业真实增长问题研究，区分市场事实、企业事实与待验证假设。",
                "required_outputs": ["市场机会", "客户与渠道", "企业能力差距", "增长选择", "行动与验证指标"],
                "governance": "不得仅凭公开行业信息替代企业一手资料；Scorecard与Action Plan必须经过人工确认。",
            },
            inputs={
                "required": ["industry", "region", "research_objective", "time_horizon", "target_company", "company_strategy_objective"]
            },
        ),
        BuiltinScenarioPack(
            descriptor=ExtensionDescriptor(
                extension_id="pe_vc",
                version="1.0.0",
                display_name="PE/VC 赛道研判",
                description="用于赛道筛选、投资假设、标的地图与风险验证。",
                capabilities=("investment-thesis", "target-landscape", "risk-diligence"),
            ),
            instructions={
                "decision_lens": "服务投资筛选而非给出无条件投资建议；明确投资假设、反证、退出条件和待尽调事项。",
                "required_outputs": ["赛道吸引力", "价值池", "标的地图", "投资假设", "主要风险", "尽调问题"],
                "governance": "市场规模与增长数据必须标注口径；估值、回报和交易判断缺少输入时必须列为未决。",
            },
            inputs={"required": ["industry", "region", "research_objective", "time_horizon"]},
        ),
    )
