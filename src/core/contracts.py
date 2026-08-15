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


@runtime_checkable
class ScenarioPack(Protocol):
    """A PE/VC, growth-strategy or future scenario-specific workflow pack."""

    descriptor: ExtensionDescriptor

    def research_instructions(self) -> Mapping[str, Any]: ...

    def required_inputs(self) -> Mapping[str, Any]: ...


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
