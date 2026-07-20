from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Callable, Mapping

import httpx


_TRUE_VALUES = {"1", "true", "yes", "on"}

_ALLOWED_MODES = {
    "auto",
    "single",
    "review",
    "council",
}

_ALLOWED_ALIASES = {
    "helpus-fast",
    "helpus-general",
    "helpus-reasoner",
    "helpus-code",
    "helpus-vision",
    "helpus-verifier",
    "helpus-embedding",
}


@dataclass(frozen=True)
class MultiAIConfig:
    enabled: bool
    base_url: str
    api_key: str
    timeout_seconds: float
    mode: str
    fallback_to_legacy: bool
    default_alias: str


@dataclass(frozen=True)
class MultiAIResult:
    text: str
    tokens: int
    latency_ms: int
    alias: str
    mode: str
    request_id: str | None
    provider: str = "multi_ai"


class MultiAIProviderError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _as_bool(
    value: str | None,
    default: bool = False,
) -> bool:
    if value is None:
        return default

    return value.lower().strip() in _TRUE_VALUES


def _as_timeout(
    value: str | None,
) -> float:
    try:
        timeout = float(value or 180)
    except (TypeError, ValueError):
        return 180.0

    if timeout <= 0 or timeout > 900:
        return 180.0

    return timeout


def _as_non_negative_int(
    value: Any,
    default: int = 0,
) -> int:
    if isinstance(value, bool):
        return default

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    return max(parsed, 0)


def load_multi_ai_config(
    env: Mapping[str, str] | None = None,
) -> MultiAIConfig:
    source = env if env is not None else os.environ

    return MultiAIConfig(
        enabled=_as_bool(
            source.get("HELPUS_MULTI_AI_ENABLED")
        ),
        base_url=(
            source.get("HELPUS_MULTI_AI_BASE_URL")
            or "http://127.0.0.1:8080"
        ).rstrip("/"),
        api_key=(
            source.get("HELPUS_MULTI_AI_API_KEY")
            or ""
        ).strip(),
        timeout_seconds=_as_timeout(
            source.get("HELPUS_MULTI_AI_TIMEOUT_SECONDS")
        ),
        mode=(
            source.get("HELPUS_MULTI_AI_MODE")
            or "auto"
        ).lower().strip(),
        fallback_to_legacy=_as_bool(
            source.get(
                "HELPUS_MULTI_AI_FALLBACK_TO_LEGACY"
            ),
            default=True,
        ),
        default_alias=(
            source.get("HELPUS_MULTI_AI_DEFAULT_ALIAS")
            or "helpus-general"
        ).lower().strip(),
    )


def sanitize_multi_ai_error(
    exc: BaseException,
) -> str:
    if isinstance(exc, MultiAIProviderError):
        return exc.code

    if isinstance(
        exc,
        (
            httpx.TimeoutException,
            asyncio.TimeoutError,
            TimeoutError,
        ),
    ):
        return "multi_ai_timeout"

    if isinstance(exc, httpx.RequestError):
        return "multi_ai_network_error"

    return "multi_ai_unavailable"


def normalize_multi_ai_response(
    data: Any,
    config: MultiAIConfig,
    measured_latency_ms: int,
) -> MultiAIResult:
    if not isinstance(data, dict):
        raise MultiAIProviderError(
            "multi_ai_invalid_json"
        )

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise MultiAIProviderError(
            "multi_ai_invalid_response"
        ) from None

    if isinstance(content, str):
        text = content.strip()
    elif content is None:
        text = ""
    else:
        text = json.dumps(
            content,
            ensure_ascii=False,
        ).strip()

    if not text:
        raise MultiAIProviderError(
            "multi_ai_empty_response"
        )

    usage = data.get("usage")
    usage = usage if isinstance(usage, dict) else {}

    helpus_metadata = data.get("_helpus")
    helpus_metadata = (
        helpus_metadata
        if isinstance(helpus_metadata, dict)
        else {}
    )

    route = helpus_metadata.get("route")
    route = route if isinstance(route, dict) else {}

    alias = str(
        route.get("primary")
        or config.default_alias
    ).strip()

    if alias not in _ALLOWED_ALIASES:
        alias = config.default_alias

    mode = str(
        route.get("mode")
        or config.mode
    ).lower().strip()

    if mode not in _ALLOWED_MODES:
        mode = config.mode

    request_id_value = helpus_metadata.get(
        "request_id"
    )

    request_id = (
        str(request_id_value).strip()
        if request_id_value
        else None
    )

    return MultiAIResult(
        text=text,
        tokens=_as_non_negative_int(
            usage.get("completion_tokens")
        ),
        latency_ms=_as_non_negative_int(
            helpus_metadata.get("elapsed_ms"),
            measured_latency_ms,
        ),
        alias=alias,
        mode=mode,
        request_id=request_id,
    )


class MultiAIProvider:
    def __init__(
        self,
        config: MultiAIConfig | None = None,
        client_factory: Callable[..., Any] = httpx.AsyncClient,
    ):
        self.config = config or load_multi_ai_config()
        self.client_factory = client_factory

        if self.config.mode not in _ALLOWED_MODES:
            raise MultiAIProviderError(
                "multi_ai_invalid_mode"
            )

        if (
            self.config.default_alias
            not in _ALLOWED_ALIASES
        ):
            raise MultiAIProviderError(
                "multi_ai_invalid_alias"
            )

        if not self.config.base_url:
            raise MultiAIProviderError(
                "multi_ai_invalid_base_url"
            )

    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> MultiAIResult:
        if not self.config.enabled:
            raise MultiAIProviderError(
                "multi_ai_disabled"
            )

        if not prompt or not prompt.strip():
            raise MultiAIProviderError(
                "multi_ai_empty_prompt"
            )

        headers = {
            "Content-Type": "application/json",
        }

        if self.config.api_key:
            headers["Authorization"] = (
                "Bearer " +
                self.config.api_key
            )

        payload = {
            "model": self.config.default_alias,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "helpus_mode": self.config.mode,
        }

        started = time.perf_counter()

        async with self.client_factory(
            timeout=self.config.timeout_seconds
        ) as client:
            response = await client.post(
                (
                    self.config.base_url +
                    "/v1/chat/completions"
                ),
                headers=headers,
                json=payload,
            )

        measured_latency_ms = int(
            (time.perf_counter() - started) *
            1000
        )

        status_code = _as_non_negative_int(
            getattr(
                response,
                "status_code",
                500,
            ),
            500,
        )

        if status_code >= 400:
            raise MultiAIProviderError(
                "multi_ai_http_error"
            )

        try:
            data = response.json()
        except Exception:
            raise MultiAIProviderError(
                "multi_ai_invalid_json"
            ) from None

        return normalize_multi_ai_response(
            data=data,
            config=self.config,
            measured_latency_ms=measured_latency_ms,
        )
