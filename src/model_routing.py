"""Task-level model policy shared by API, workers and future plugin channels."""

from __future__ import annotations

from enum import StrEnum


class ModelProfile(StrEnum):
    FAST = "fast"
    STANDARD = "standard"
    DEEP = "deep"
    SYNTHESIS = "synthesis"


TASK_MODEL_PROFILES: dict[str, ModelProfile] = {
    "scenario_interview": ModelProfile.FAST,
    "research_brief": ModelProfile.STANDARD,
    "research_plan": ModelProfile.STANDARD,
    "evidence_collection": ModelProfile.FAST,
    "reviewer_revision": ModelProfile.STANDARD,
    "industry_analysis": ModelProfile.DEEP,
    "future_intelligence": ModelProfile.DEEP,
    "company_scorecard": ModelProfile.DEEP,
    "action_plan": ModelProfile.DEEP,
    "adaptive_plan": ModelProfile.DEEP,
    "report_generation": ModelProfile.SYNTHESIS,
}


MODEL_PROFILE_POLICY = {
    ModelProfile.FAST: {
        "model_role": "fast",
        "thinking": "disabled",
        "reasoning_effort": None,
        "max_tokens": 2000,
    },
    ModelProfile.STANDARD: {
        "model_role": "fast",
        "thinking": "enabled",
        "reasoning_effort": "low",
        "max_tokens": 4000,
    },
    ModelProfile.DEEP: {
        "model_role": "reasoning",
        "thinking": "enabled",
        "reasoning_effort": "high",
        "max_tokens": 12000,
    },
    ModelProfile.SYNTHESIS: {
        "model_role": "fast",
        "thinking": "disabled",
        "reasoning_effort": None,
        "max_tokens": 12000,
    },
}
