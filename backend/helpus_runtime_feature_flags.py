from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

ADAPTER_ENABLED_FLAG = "HELPUSAI_CONVERSATION_ADAPTER_ENABLED"
ADAPTER_FORCE_FLAG = "HELPUSAI_CONVERSATION_ADAPTER_FORCE"

def parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    return default

@dataclass(frozen=True)
class HelpUSRuntimeFeatureFlags:
    conversation_adapter_enabled: bool = False
    conversation_adapter_force: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["adapter_enabled_flag"] = ADAPTER_ENABLED_FLAG
        data["adapter_force_flag"] = ADAPTER_FORCE_FLAG
        data["default_enabled"] = False
        data["safe_default"] = not self.conversation_adapter_enabled
        return data

def load_helpus_runtime_feature_flags(env: Mapping[str, str] | None = None) -> HelpUSRuntimeFeatureFlags:
    source = env or {}
    return HelpUSRuntimeFeatureFlags(
        conversation_adapter_enabled=parse_bool(source.get(ADAPTER_ENABLED_FLAG), default=False),
        conversation_adapter_force=parse_bool(source.get(ADAPTER_FORCE_FLAG), default=False),
    )
