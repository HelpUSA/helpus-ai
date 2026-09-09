from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_conversation_api_adapter import adapt_helpus_conversation_message


FEATURE_FLAG_NAME = "HELPUSAI_CONVERSATION_ADAPTER_ENABLED"


@dataclass(frozen=True)
class HelpUSChatEndpointWiringResult:
    enabled: bool
    feature_flag: str
    user_message: str
    response_text: str
    used_adapter: bool
    reason: str
    safety: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HelpUSChatEndpointWiring:
    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    def handle_message(
        self,
        user_message: str,
        *,
        primary_response: str = "",
        project_id: str = "helpusai",
        force_adapter: bool = False,
    ) -> HelpUSChatEndpointWiringResult:
        message = user_message.strip()
        if not self.enabled:
            return HelpUSChatEndpointWiringResult(
                enabled=False,
                feature_flag=FEATURE_FLAG_NAME,
                user_message=message,
                response_text=primary_response,
                used_adapter=False,
                reason="feature flag disabled; primary response preserved",
                safety=self._default_safety(),
                metadata={"project_id": project_id},
            )

        adapter_result = adapt_helpus_conversation_message(
            message,
            project_id=project_id,
            force=force_adapter,
        )

        if not adapter_result.get("should_use_adapter", False):
            return HelpUSChatEndpointWiringResult(
                enabled=True,
                feature_flag=FEATURE_FLAG_NAME,
                user_message=message,
                response_text=primary_response,
                used_adapter=False,
                reason=str(adapter_result.get("reason", "adapter declined")),
                safety=dict(adapter_result.get("safety", self._default_safety())),
                metadata=dict(adapter_result.get("metadata", {"project_id": project_id})),
            )

        return HelpUSChatEndpointWiringResult(
            enabled=True,
            feature_flag=FEATURE_FLAG_NAME,
            user_message=message,
            response_text=str(adapter_result.get("response_text", "")),
            used_adapter=True,
            reason=str(adapter_result.get("reason", "adapter used")),
            safety=dict(adapter_result.get("safety", self._default_safety())),
            metadata=dict(adapter_result.get("metadata", {"project_id": project_id})),
        )

    def _default_safety(self) -> dict[str, Any]:
        return {
            "executes_commands": False,
            "calls_network": False,
            "changes_files": False,
            "feature_flag_required": True,
            "default_enabled": False,
        }


def handle_helpus_chat_message_guarded(
    user_message: str,
    *,
    enabled: bool = False,
    primary_response: str = "",
    project_id: str = "helpusai",
    force_adapter: bool = False,
) -> dict[str, Any]:
    return HelpUSChatEndpointWiring(enabled=enabled).handle_message(
        user_message,
        primary_response=primary_response,
        project_id=project_id,
        force_adapter=force_adapter,
    ).to_dict()
