from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from typing import Mapping


_TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LocalAIConfig:
    enabled: bool
    base_url: str
    model: str
    timeout_seconds: float


def _as_bool(value: str | None) -> bool:
    return (value or "").lower().strip() in _TRUE_VALUES


def _as_timeout(value: str | None, default: float = 15.0) -> float:
    try:
        parsed = float(value or default)
    except (TypeError, ValueError):
        return default
    if parsed <= 0 or parsed > 120:
        return default
    return parsed


def load_local_ai_config(env: Mapping[str, str] | None = None) -> LocalAIConfig:
    source = env if env is not None else os.environ
    return LocalAIConfig(
        enabled=_as_bool(source.get("HELPUS_LOCAL_AI_ENABLED")),
        base_url=(source.get("HELPUS_LOCAL_AI_BASE_URL") or "http://127.0.0.1:11434").rstrip("/"),
        model=(source.get("HELPUS_LOCAL_AI_MODEL") or "local-analysis").strip(),
        timeout_seconds=_as_timeout(source.get("HELPUS_LOCAL_AI_TIMEOUT_SECONDS")),
    )


def is_local_ai_available(config: LocalAIConfig | None = None) -> bool:
    value = config or load_local_ai_config()
    return bool(value.enabled and value.base_url and value.model)


def build_local_ai_analysis_request(prompt: str, config: LocalAIConfig | None = None) -> dict:
    value = config or load_local_ai_config()
    if not prompt or not prompt.strip():
        raise ValueError("prompt must be non-empty")

    if not is_local_ai_available(value):
        return {
            "enabled": False,
            "provider": "local_ai",
            "mode": "analysis_only",
            "reason": "disabled_by_default_or_incomplete_config",
            "can_execute_commands": False,
            "request": None,
        }

    return {
        "enabled": True,
        "provider": "local_ai",
        "mode": "analysis_only",
        "reason": "ready",
        "can_execute_commands": False,
        "request": {
            "method": "POST",
            "url": value.base_url + "/v1/chat/completions",
            "timeout_seconds": value.timeout_seconds,
            "json": {
                "model": value.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You analyze HelpUS AI project state. Never execute commands.",
                    },
                    {
                        "role": "user",
                        "content": prompt.strip(),
                    },
                ],
                "temperature": 0.2,
            },
        },
    }


def render_local_ai_summary(config: LocalAIConfig | None = None) -> str:
    value = config or load_local_ai_config()
    status = "enabled" if is_local_ai_available(value) else "disabled"
    return (
        "local_ai_status={status} enabled={enabled} model={model} "
        "base_url={base_url} timeout_seconds={timeout} mode=analysis_only can_execute_commands=False"
    ).format(
        status=status,
        enabled=value.enabled,
        model=value.model,
        base_url=value.base_url,
        timeout=value.timeout_seconds,
    )


def export_local_ai_config(config: LocalAIConfig | None = None) -> dict:
    return asdict(config or load_local_ai_config())
