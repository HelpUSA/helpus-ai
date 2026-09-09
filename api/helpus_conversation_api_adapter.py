from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_conversation_response_composer import compose_helpus_response


COMMAND_INTENT_MARKERS = (
    "comando",
    "command",
    "script",
    "powershell",
    "git status",
    "git diff",
    "git push",
    "smoke",
    "validar",
    "valide",
    "rode",
    "executar",
    "execute",
    "patch",
    "micro",
    "repo",
    "estado do projeto",
    "verifique o estado",
)


@dataclass(frozen=True)
class HelpUSConversationAdapterResult:
    should_use_adapter: bool
    response_text: str
    source: str
    reason: str
    safety: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HelpUSConversationAPIAdapter:
    def adapt(
        self,
        user_message: str,
        *,
        project_id: str = "helpusai",
        force: bool = False,
    ) -> HelpUSConversationAdapterResult:
        message = user_message.strip()
        if not message:
            return HelpUSConversationAdapterResult(
                should_use_adapter=False,
                response_text="",
                source="conversation_api_adapter",
                reason="empty message",
                safety=self._default_safety(),
                metadata={"project_id": project_id},
            )

        should_use = force or self._looks_like_command_or_project_intent(message)
        if not should_use:
            return HelpUSConversationAdapterResult(
                should_use_adapter=False,
                response_text="",
                source="conversation_api_adapter",
                reason="normal chat message; let primary model answer",
                safety=self._default_safety(),
                metadata={"project_id": project_id},
            )

        composed = compose_helpus_response(message)
        response_text = str(composed.get("message", ""))
        metadata = {
            "project_id": project_id,
            "risk_level": composed.get("risk_level"),
            "decision": composed.get("decision"),
            "action": composed.get("action"),
            "execution_allowed": composed.get("execution_allowed"),
            "requires_human_approval": composed.get("requires_human_approval"),
            "next_step": composed.get("next_step"),
        }

        return HelpUSConversationAdapterResult(
            should_use_adapter=True,
            response_text=response_text,
            source="conversation_response_composer",
            reason="command or project operations intent detected",
            safety=self._default_safety(),
            metadata=metadata,
        )

    def _looks_like_command_or_project_intent(self, message: str) -> bool:
        normalized = message.lower()
        return any(marker in normalized for marker in COMMAND_INTENT_MARKERS)

    def _default_safety(self) -> dict[str, Any]:
        return {
            "executes_commands": False,
            "calls_network": False,
            "changes_files": False,
            "requires_review_before_execution": True,
            "stop_on_failure": True,
        }


def adapt_helpus_conversation_message(
    user_message: str,
    *,
    project_id: str = "helpusai",
    force: bool = False,
) -> dict[str, Any]:
    return HelpUSConversationAPIAdapter().adapt(
        user_message,
        project_id=project_id,
        force=force,
    ).to_dict()
