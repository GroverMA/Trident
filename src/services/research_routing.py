"""Policy-driven research-path routing with no scenario-name branches."""

from __future__ import annotations

from src.core.registry import ExtensionRegistry
from src.models.research_routing import ResearchRouteDecision
from src.state.project import ProjectState, ResearchPath


class ScenarioResearchRouter:
    def __init__(self, packs: ExtensionRegistry) -> None:
        self._packs = packs

    def route(
        self,
        project: ProjectState,
        *,
        available_materials: list[str],
        has_existing_report: bool = False,
    ) -> ProjectState:
        pack = self._packs.get(project.scenario_pack, project.scenario_pack_version)
        policy = dict(pack.research_route_policy())
        materials = list(dict.fromkeys(item.strip() for item in available_materials if item.strip()))
        threshold = max(1, int(policy.get("review_material_threshold", 1)))
        allow_review = bool(policy.get("allow_review_first", True))
        default = ResearchPath(str(policy.get("default_path", ResearchPath.BUILD_FIRST.value)))
        enough_for_review = len(materials) >= threshold or has_existing_report
        insufficient = ResearchPath(str(policy.get("insufficient_material_path", default.value)))
        selected = ResearchPath.REVIEW_FIRST if allow_review and enough_for_review else insufficient
        supplemental = bool(policy.get("supplemental_gap_research", True))
        mode_label = "审阅式 + 缺口构建研究" if selected == ResearchPath.REVIEW_FIRST and supplemental else (
            "审阅式研究" if selected == ResearchPath.REVIEW_FIRST else "构建式研究"
        )
        rationale = [str(policy.get("reason") or "根据场景默认研究策略选择主路径。")]
        rationale.append(
            f"已登记{len(materials)}类材料，审阅式门槛为{threshold}类。"
            if allow_review else "该场景要求独立构建外部行业证据，内部资料仅作为场景输入。"
        )
        decision = ResearchRouteDecision(
            scenario_id=project.scenario_pack,
            primary_path=selected,
            supplemental_gap_research=supplemental,
            mode_label=mode_label,
            rationale=rationale,
            available_materials=materials,
            data_scope=dict(pack.data_scope_policy()),
        )
        return project.model_copy(update={"research_path": selected, "research_route_artifact": decision})
