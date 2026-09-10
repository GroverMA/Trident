"""HKGAI Modelhub implementation using its OpenAI-compatible REST API."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

import requests

from src.config import Settings
from src.providers.base import ChatMessage, ModelProvider, ModelResponse, ProviderError
from src.observability.telemetry import record_model_usage


class HKGAIModelProvider(ModelProvider):
    def __init__(
        self,
        settings: Settings,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self.settings = settings
        self.session = session or requests.Session()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.model_api_key}",
            "Content-Type": "application/json",
        }

    def list_models(self) -> list[str]:
        payload = self._request_json(
            "GET", f"{self.settings.model_base_url}/v1/models"
        )
        records = payload.get("data", [])
        if not isinstance(records, list):
            raise ProviderError("Modelhub returned an invalid model list")
        return [
            str(record["id"])
            for record in records
            if isinstance(record, dict) and record.get("id")
        ]

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        enable_thinking: bool = False,
        reasoning_effort: str | None = None,
        json_mode: bool = False,
    ) -> ModelResponse:
        structured_budget = 8000 if json_mode else 0
        body: dict[str, Any] = {
            "model": self.settings.model_name,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            "stream": False,
            "max_tokens": max(self.settings.model_max_tokens, structured_budget),
        }
        is_deepseek = (
            "api.deepseek.com" in self.settings.model_base_url
            or self.settings.model_name.lower().startswith("deepseek-")
        )
        if json_mode and is_deepseek:
            body["response_format"] = {"type": "json_object"}
        if is_deepseek:
            body["thinking"] = {
                "type": "enabled" if enable_thinking else "disabled"
            }
            if enable_thinking:
                body["reasoning_effort"] = (
                    reasoning_effort or self.settings.model_reasoning_effort
                )
        elif enable_thinking:
            body.update(
                {
                    "reasoning_effort": (
                        reasoning_effort or self.settings.model_reasoning_effort
                    ),
                    "include_reasoning": True,
                    "chat_template_kwargs": {"enable_thinking": True},
                }
            )

        started_at = datetime.now(UTC)
        started_clock = perf_counter()
        payload = self._request_json(
            "POST",
            f"{self.settings.model_base_url}/v1/chat/completions",
            json_body=body,
        )
        try:
            choice = payload["choices"][0]
            message = choice["message"]
            content = message.get("content", "")
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Modelhub returned an invalid completion") from exc

        usage = payload.get("usage", {})
        result = ModelResponse(
            content=str(content or ""),
            reasoning=(
                str(message.get("reasoning") or message.get("reasoning_content"))
                if message.get("reasoning") is not None
                or message.get("reasoning_content") is not None
                else None
            ),
            model=str(payload.get("model") or self.settings.model_name),
            usage=usage if isinstance(usage, dict) else {},
        )
        record_model_usage(
            model=result.model or self.settings.model_name,
            usage=result.usage,
            started_at=started_at,
            duration_ms=round((perf_counter() - started_clock) * 1000),
        )
        return result

    def complete_json(
        self,
        messages: list[ChatMessage],
        *,
        enable_thinking: bool = False,
    ) -> tuple[dict[str, Any], ModelResponse]:
        attempt_messages = list(messages)
        for attempt in range(2):
            response = self.complete(
                attempt_messages,
                enable_thinking=enable_thinking,
                json_mode=True,
            )
            candidates = [response.content]
            # Some OpenAI-compatible gateways place the final answer in the
            # reasoning field when thinking mode is enabled. Prefer content,
            # but accept reasoning as a compatibility fallback when it
            # contains the requested JSON object.
            if response.reasoning:
                candidates.append(response.reasoning)

            for candidate in candidates:
                parsed = self._extract_json_object(candidate)
                if parsed is not None:
                    return parsed, response
            if attempt == 0:
                attempt_messages.extend(
                    [
                        ChatMessage(
                            role="assistant",
                            content=(response.content or response.reasoning or "")[-4000:],
                        ),
                        ChatMessage(
                            role="user",
                            content=(
                                "上一次输出不是完整合法的 JSON 对象。请立即重新输出完整 JSON；"
                                "不要解释、不要使用 Markdown 代码围栏、不要省略结尾括号。"
                            ),
                        ),
                    ]
                )
        raise ProviderError("Modelhub did not return valid JSON")

    @staticmethod
    def _extract_json_object(text: str | None) -> dict[str, Any] | None:
        """Extract a JSON object from common LLM response wrappers.

        Besides plain JSON, models may add an explanation, a Markdown fence,
        or thinking tags even when explicitly instructed not to. raw_decode
        lets us find the first complete object without brittle brace slicing.
        """
        candidate = str(text or "").strip().lstrip("\ufeff")
        if not candidate:
            return None

        try:
            direct = json.loads(candidate)
        except json.JSONDecodeError:
            direct = None
        if isinstance(direct, dict):
            return direct

        decoder = json.JSONDecoder()
        for index, character in enumerate(candidate):
            if character != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(candidate[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self.session.request(
                method,
                url,
                headers=self._headers,
                json=json_body,
                timeout=self.settings.model_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.Timeout as exc:
            raise ProviderError("Modelhub request timed out") from exc
        except requests.RequestException as exc:
            status = getattr(exc.response, "status_code", None)
            detail = f" (HTTP {status})" if status else ""
            raise ProviderError(f"Modelhub request failed{detail}") from exc
        except ValueError as exc:
            raise ProviderError("Modelhub returned non-JSON data") from exc
        if not isinstance(payload, dict):
            raise ProviderError("Modelhub returned an invalid JSON object")
        return payload
