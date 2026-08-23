"""Stable delivery contracts shared by Feishu, Copilot and future channels.

An integration surface is an adapter around the Research Core. It does not own
scenario logic, prompts, evidence rules or project state. This prevents a chat
platform integration from becoming a second, simplified implementation of
Trident's research workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OperationAvailability = Literal["available", "planned_job_api", "planned_auth"]
InteractionMode = Literal["full_workspace", "conversational_companion", "api_action"]


@dataclass(frozen=True, slots=True)
class IntegrationOperation:
    operation_id: str
    purpose: str
    availability: OperationAvailability
    execution: Literal["synchronous", "asynchronous_job", "deep_link"]
    mutates_state: bool = False
    requires_human_confirmation: bool = False


@dataclass(frozen=True, slots=True)
class IntegrationSurface:
    surface_id: str
    display_name: str
    interaction_mode: InteractionMode
    recommended_scope: str
    supports_full_workspace: bool
    identity_strategy: str
    response_strategy: str
    operations: tuple[IntegrationOperation, ...]

    def as_dict(self) -> dict:
        return {
            "surface_id": self.surface_id,
            "display_name": self.display_name,
            "interaction_mode": self.interaction_mode,
            "recommended_scope": self.recommended_scope,
            "supports_full_workspace": self.supports_full_workspace,
            "identity_strategy": self.identity_strategy,
            "response_strategy": self.response_strategy,
            "operations": [
                {
                    "operation_id": operation.operation_id,
                    "purpose": operation.purpose,
                    "availability": operation.availability,
                    "execution": operation.execution,
                    "mutates_state": operation.mutates_state,
                    "requires_human_confirmation": operation.requires_human_confirmation,
                }
                for operation in self.operations
            ],
        }
