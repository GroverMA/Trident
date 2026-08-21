"""Stable extension contracts for scenario, industry and algorithm teams.

These contracts intentionally contain no Streamlit, FastAPI or provider-specific
types.  A future API server, background worker or embedded plugin can therefore
use the same research core as the current demonstration UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ExtensionDescriptor:
    extension_id: str
    version: str
    display_name: str
    description: str = ""
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScenarioManifest:
    """Version and compatibility metadata for an executable scenario pack."""

    scenario_id: str
    version: str
    research_core_version: str = "1.0.0"
    deprecated: bool = False
    replaces: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScenarioWorkflowNode:
    """One declarative step executed by the shared workflow runner."""

    node_id: str
    capability: str
    depends_on: tuple[str, ...] = ()
    review_gate: str | None = None
    checkpoint: bool = True


@runtime_checkable
class ScenarioPack(Protocol):
    """A PE/VC, growth-strategy or future scenario-specific workflow pack."""

    descriptor: ExtensionDescriptor

    def manifest(self) -> ScenarioManifest: ...

    def research_instructions(self) -> Mapping[str, Any]: ...

    def required_inputs(self) -> Mapping[str, Any]: ...

    def workflow(self) -> tuple[ScenarioWorkflowNode, ...]: ...

    def interview_policy(self) -> Mapping[str, Any]: ...

    def evidence_policy(self) -> Mapping[str, Any]: ...

    def review_gates(self) -> Mapping[str, Any]: ...

    def output_schema(self) -> Mapping[str, Any]: ...

    def evaluation_rubric(self) -> Mapping[str, Any]: ...

    def report_template(self) -> Mapping[str, Any]: ...

    def ui_schema(self) -> Mapping[str, Any]: ...

    def feedback_policy(self) -> Mapping[str, Any]: ...

    def research_route_policy(self) -> Mapping[str, Any]: ...

    def data_scope_policy(self) -> Mapping[str, Any]: ...


@runtime_checkable
class IndustryPack(Protocol):
    """Optional industry vocabulary, benchmarks and specialist methods."""

    descriptor: ExtensionDescriptor

    def research_context(self) -> Mapping[str, Any]: ...


@runtime_checkable
class AlgorithmStrategy(Protocol):
    """A replaceable algorithm used for one bounded analytical capability."""

    descriptor: ExtensionDescriptor

    def execute(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


@runtime_checkable
class ArtifactEvaluator(Protocol):
    """Scores a candidate output without changing the production workflow."""

    descriptor: ExtensionDescriptor

    def evaluate(
        self,
        *,
        artifact_type: str,
        artifact: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Mapping[str, float]: ...


@dataclass(frozen=True, slots=True)
class ResearchEvent:
    event_type: str
    project_id: str
    run_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class EventSink(Protocol):
    """Receives privacy-safe events for audit, evaluation and later learning."""

    def record(self, event: ResearchEvent) -> None: ...


class NullEventSink:
    def record(self, event: ResearchEvent) -> None:
        del event
