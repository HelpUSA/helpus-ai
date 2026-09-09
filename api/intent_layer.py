from __future__ import annotations

from typing import Any

from command_builder import CommandBuilder
from preflight_validator import PreflightValidator


class IntentError(Exception):
    pass


class IntentLayer:
    @staticmethod
    def build(intent: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(intent, dict):
            raise IntentError("Intent must be dict")

        intent_type = intent.get("type")

        if intent_type == "send_chat":
            envelope = CommandBuilder.build_send_chat(
                source_chat_id=intent.get("source_chat_id"),
                target_chat_id=intent.get("target_chat_id"),
                message=intent.get("message"),
                conversation_id=intent.get("conversation_id", "helpus_intent"),
                from_agent=intent.get("from_agent", "HelpUS AI"),
                command_id=intent.get("command_id"),
            )
            PreflightValidator.validate(envelope)
            return envelope

        if intent_type == "run_command":
            envelope = CommandBuilder.build_run_command(
                source_chat_id=intent.get("source_chat_id"),
                cwd=intent.get("cwd"),
                command=intent.get("command"),
                conversation_id=intent.get("conversation_id", "helpus_intent"),
                from_agent=intent.get("from_agent", "HelpUS AI"),
                timeout_seconds=intent.get("timeout_seconds", 60),
                command_id=intent.get("command_id"),
            )
            PreflightValidator.validate(envelope)
            return envelope

        raise IntentError("Unknown intent type")
