from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from backend.helpus_chat_endpoint_wiring import handle_helpus_chat_message_guarded
from backend.helpus_runtime_feature_flags import load_helpus_runtime_feature_flags

@dataclass(frozen=True)
class HelpUSRuntimeChatResult:
    response_text: str
    used_adapter: bool
    enabled: bool
    reason: str
    safety: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def handle_helpus_runtime_chat_message(
    user_message: str,
    *,
    primary_response: str = "",
    project_id: str = "helpusai",
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source_env = env if env is not None else os.environ
    flags = load_helpus_runtime_feature_flags(source_env)
    result = handle_helpus_chat_message_guarded(
        user_message,
        enabled=flags.conversation_adapter_enabled,
        primary_response=primary_response,
        project_id=project_id,
        force_adapter=flags.conversation_adapter_force,
    )
    output = HelpUSRuntimeChatResult(
        response_text=str(result.get("response_text", "")),
        used_adapter=bool(result.get("used_adapter", False)),
        enabled=bool(result.get("enabled", False)),
        reason=str(result.get("reason", "")),
        safety=dict(result.get("safety", {})),
        metadata={**dict(result.get("metadata", {})), "feature_flags": flags.to_dict()},
    )
    return output.to_dict()
