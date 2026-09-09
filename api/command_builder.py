from __future__ import annotations

from uuid import uuid4
from typing import Any


class CommandBuilder:
    DEFAULT_LOCAL_TARGET = "gateway-brain-supervisor"

    @staticmethod
    def _new_command_id(prefix: str = "cmd") -> str:
        return f"{prefix}_{uuid4().hex}"

    @staticmethod
    def build_send_chat(
        source_chat_id: str,
        target_chat_id: str,
        message: str,
        conversation_id: str = "helpus_intent",
        from_agent: str = "HelpUS AI",
        command_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "command_id": command_id or CommandBuilder._new_command_id("send_chat"),
            "action": "send-chat-message",
            "source_chat_id": source_chat_id,
            "target_chat_id": target_chat_id,
            "delivery_kind": "inter_agent_message",
            "conversation_id": conversation_id,
            "from_agent": from_agent,
            "message": message,
            "payload": {},
        }

    @staticmethod
    def build_run_command(
        source_chat_id: str,
        cwd: str,
        command: list[str],
        conversation_id: str = "helpus_intent",
        from_agent: str = "HelpUS AI",
        timeout_seconds: int = 60,
        command_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "command_id": command_id or CommandBuilder._new_command_id("run_command"),
            "action": "run-command",
            "source_chat_id": source_chat_id,
            "target_chat_id": CommandBuilder.DEFAULT_LOCAL_TARGET,
            "delivery_kind": "local_capability",
            "conversation_id": conversation_id,
            "from_agent": from_agent,
            "payload": {
                "cwd": cwd,
                "timeout_seconds": timeout_seconds,
                "command": command,
            },
        }
