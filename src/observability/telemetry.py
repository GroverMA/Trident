"""Privacy-safe runtime telemetry for research steps and model calls."""

from __future__ import annotations

from contextvars import ContextVar, Token
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ModelCallTelemetry(BaseModel):
    call_id: str = Field(default_factory=lambda: uuid4().hex)
    model: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0


class StepRunTelemetry(BaseModel):
    run_id: str = Field(default_factory=lambda: uuid4().hex)
    project_id: str
    step: str
    task_id: str | None = None
    status: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    model_calls: list[ModelCallTelemetry] = Field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    error_type: str | None = None


def _usage_int(usage: dict[str, Any], *keys: str) -> int:
    value: Any = usage
    for key in keys:
        if not isinstance(value, dict):
            return 0
        value = value.get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


class TelemetrySpan:
    def __init__(self, project_id: str, step: str, task_id: str | None = None) -> None:
        self.project_id = project_id
        self.step = step
        self.task_id = task_id
        self.started_at = datetime.now(UTC)
        self._started_clock = perf_counter()
        self.calls: list[ModelCallTelemetry] = []
        self.error_type: str | None = None

    def record_model_call(
        self,
        *,
        model: str,
        usage: dict[str, Any],
        started_at: datetime,
        duration_ms: int,
    ) -> None:
        prompt = _usage_int(usage, "prompt_tokens") or _usage_int(usage, "input_tokens")
        completion = _usage_int(usage, "completion_tokens") or _usage_int(usage, "output_tokens")
        reasoning = (
            _usage_int(usage, "completion_tokens_details", "reasoning_tokens")
            or _usage_int(usage, "output_tokens_details", "reasoning_tokens")
            or _usage_int(usage, "reasoning_tokens")
        )
        cached = (
            _usage_int(usage, "prompt_tokens_details", "cached_tokens")
            or _usage_int(usage, "input_tokens_details", "cached_tokens")
            or _usage_int(usage, "cached_tokens")
        )
        total = _usage_int(usage, "total_tokens") or prompt + completion
        self.calls.append(ModelCallTelemetry(
            model=model,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            duration_ms=duration_ms,
            prompt_tokens=prompt,
            completion_tokens=completion,
            reasoning_tokens=reasoning,
            cached_tokens=cached,
            total_tokens=total,
        ))

    def fail(self, exc: BaseException) -> None:
        self.error_type = type(exc).__name__

    def snapshot(self) -> StepRunTelemetry:
        completed_at = datetime.now(UTC)
        return StepRunTelemetry(
            project_id=self.project_id,
            step=self.step,
            task_id=self.task_id,
            status="failed" if self.error_type else "completed",
            started_at=self.started_at,
            completed_at=completed_at,
            duration_ms=round((perf_counter() - self._started_clock) * 1000),
            model_calls=list(self.calls),
            prompt_tokens=sum(call.prompt_tokens for call in self.calls),
            completion_tokens=sum(call.completion_tokens for call in self.calls),
            reasoning_tokens=sum(call.reasoning_tokens for call in self.calls),
            cached_tokens=sum(call.cached_tokens for call in self.calls),
            total_tokens=sum(call.total_tokens for call in self.calls),
            error_type=self.error_type,
        )


_active_span: ContextVar[TelemetrySpan | None] = ContextVar(
    "trident_active_telemetry_span", default=None
)


def start_span(project_id: str, step: str, task_id: str | None = None) -> tuple[TelemetrySpan, Token]:
    span = TelemetrySpan(project_id, step, task_id)
    return span, _active_span.set(span)


def finish_span(span: TelemetrySpan, token: Token, exc: BaseException | None = None) -> StepRunTelemetry:
    if exc is not None:
        span.fail(exc)
    _active_span.reset(token)
    return span.snapshot()


def record_model_usage(
    *, model: str, usage: dict[str, Any], started_at: datetime, duration_ms: int
) -> None:
    span = _active_span.get()
    if span is not None:
        span.record_model_call(
            model=model,
            usage=usage,
            started_at=started_at,
            duration_ms=duration_ms,
        )
