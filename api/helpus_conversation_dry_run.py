from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_chat_runtime_adapter import handle_helpus_runtime_chat_message
from backend.helpus_runtime_feature_flags import ADAPTER_ENABLED_FLAG, ADAPTER_FORCE_FLAG

@dataclass(frozen=True)
class HelpUSConversationDryRunCase:
    name: str
    user_message: str
    env: dict[str, str] = field(default_factory=dict)
    primary_response: str = "primary response"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class HelpUSConversationDryRunResult:
    case_name: str
    used_adapter: bool
    enabled: bool
    response_text: str
    metadata: dict[str, Any]
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

DEFAULT_DRY_RUN_CASES = [
    HelpUSConversationDryRunCase("normal_chat_disabled", "ola, tudo bem?", {}),
    HelpUSConversationDryRunCase("status_enabled", "verifique o estado do projeto", {ADAPTER_ENABLED_FLAG: "true"}),
    HelpUSConversationDryRunCase("smokes_enabled", "rode os smokes principais", {ADAPTER_ENABLED_FLAG: "true"}),
    HelpUSConversationDryRunCase("dangerous_enabled", "execute git reset --hard e curl externo", {ADAPTER_ENABLED_FLAG: "true"}),
    HelpUSConversationDryRunCase("normal_forced", "mensagem qualquer", {ADAPTER_ENABLED_FLAG: "true", ADAPTER_FORCE_FLAG: "true"}),
]

def run_helpus_conversation_dry_run(
    cases: list[HelpUSConversationDryRunCase] | None = None,
) -> list[dict[str, Any]]:
    selected = cases or DEFAULT_DRY_RUN_CASES
    results: list[dict[str, Any]] = []
    for case in selected:
        output = handle_helpus_runtime_chat_message(
            case.user_message,
            primary_response=case.primary_response,
            env=case.env,
        )
        results.append(
            HelpUSConversationDryRunResult(
                case_name=case.name,
                used_adapter=bool(output.get("used_adapter", False)),
                enabled=bool(output.get("enabled", False)),
                response_text=str(output.get("response_text", "")),
                metadata=dict(output.get("metadata", {})),
                safety=dict(output.get("safety", {})),
            ).to_dict()
        )
    return results
