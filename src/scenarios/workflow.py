"""Generic scenario workflow planning without business-name conditionals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.core.contracts import ScenarioPack, ScenarioWorkflowNode
from src.core.registry import ExtensionRegistry


class ScenarioContractError(ValueError):
    pass


class ScenarioInputError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ScenarioExecutionPlan:
    scenario_id: str
    scenario_version: str
    research_core_version: str
    nodes: tuple[ScenarioWorkflowNode, ...]


class ScenarioWorkflowRunner:
    """Validate and order any registered pack without knowing its business name."""

    def __init__(self, registry: ExtensionRegistry[ScenarioPack]) -> None:
        self.registry = registry

    def plan(
        self,
        scenario_id: str,
        version: str,
        inputs: Mapping[str, Any],
    ) -> ScenarioExecutionPlan:
        pack = self.registry.get(scenario_id, version)
        self._validate_inputs(pack, inputs)
        nodes = self._ordered_nodes(pack.workflow())
        manifest = pack.manifest()
        if manifest.scenario_id != pack.descriptor.extension_id:
            raise ScenarioContractError("manifest scenario id must match descriptor")
        if manifest.version != pack.descriptor.version:
            raise ScenarioContractError("manifest version must match descriptor")
        return ScenarioExecutionPlan(
            scenario_id=manifest.scenario_id,
            scenario_version=manifest.version,
            research_core_version=manifest.research_core_version,
            nodes=nodes,
        )

    @staticmethod
    def _validate_inputs(pack: ScenarioPack, inputs: Mapping[str, Any]) -> None:
        required = tuple(pack.required_inputs().get("required", ()))
        missing = [key for key in required if not str(inputs.get(key, "")).strip()]
        if missing:
            raise ScenarioInputError(
                "missing required scenario inputs: " + ", ".join(missing)
            )

    @staticmethod
    def _ordered_nodes(
        nodes: tuple[ScenarioWorkflowNode, ...],
    ) -> tuple[ScenarioWorkflowNode, ...]:
        by_id = {node.node_id: node for node in nodes}
        if len(by_id) != len(nodes):
            raise ScenarioContractError("workflow node ids must be unique")
        for node in nodes:
            unknown = set(node.depends_on) - set(by_id)
            if unknown:
                raise ScenarioContractError(
                    f"workflow node {node.node_id} has unknown dependencies: "
                    + ", ".join(sorted(unknown))
                )

        pending = dict(by_id)
        ordered: list[ScenarioWorkflowNode] = []
        completed: set[str] = set()
        while pending:
            ready = sorted(
                (node for node in pending.values() if set(node.depends_on) <= completed),
                key=lambda item: item.node_id,
            )
            if not ready:
                raise ScenarioContractError("workflow dependencies contain a cycle")
            for node in ready:
                ordered.append(node)
                completed.add(node.node_id)
                pending.pop(node.node_id)
        return tuple(ordered)
