from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    pass


class PreflightValidator:
    MAX_MESSAGE_SIZE = 8000
    MAX_COMMAND_PARTS = 64
    MAX_COMMAND_PART_SIZE = 4000
    MAX_TIMEOUT_SECONDS = 900

    FORBIDDEN_DELIVERY_KINDS = {"local_inter_agent_message"}
    FORBIDDEN_TARGETS = {"local"}
    FORBIDDEN_PLACEHOLDERS = {
        "{ JSON PURO }",
        "{ JSON_VALIDO_AQUI }",
        "{ exemplo }",
        "JSON_VALIDO_AQUI",
        "JSON PURO",
    }
    INVISIBLE_CHARS = ("​", "‌", "‍", "﻿")

    @classmethod
    def validate(cls, envelope: dict[str, Any]) -> bool:
        if not isinstance(envelope, dict):
            raise ValidationError("Envelope must be dict")

        cls._validate_common(envelope)
        action = envelope.get("action")

        if action == "send-chat-message":
            cls._validate_send_chat(envelope)
            return True

        if action == "run-command":
            cls._validate_run_command(envelope)
            return True

        raise ValidationError("Unknown action")

    @classmethod
    def _validate_common(cls, envelope: dict[str, Any]) -> None:
        for field in ("command_id", "action", "source_chat_id", "target_chat_id", "delivery_kind"):
            if not envelope.get(field):
                raise ValidationError(f"Missing field: {field}")

        if envelope.get("target_chat_id") in cls.FORBIDDEN_TARGETS:
            raise ValidationError("Invalid target_chat_id")

        if envelope.get("delivery_kind") in cls.FORBIDDEN_DELIVERY_KINDS:
            raise ValidationError("Invalid delivery_kind")

        for field in ("command_id", "source_chat_id", "target_chat_id", "conversation_id", "from_agent"):
            value = envelope.get(field)
            if isinstance(value, str):
                cls._reject_bad_text(value, field)

    @classmethod
    def _validate_send_chat(cls, envelope: dict[str, Any]) -> None:
        for field in ("source_chat_id", "target_chat_id", "message"):
            if not envelope.get(field):
                raise ValidationError(f"Missing field: {field}")

        if envelope.get("delivery_kind") != "inter_agent_message":
            raise ValidationError("Invalid delivery_kind for send-chat-message")

        message = envelope.get("message")
        if not isinstance(message, str) or not message.strip():
            raise ValidationError("Message must be non-empty string")

        if len(message) > cls.MAX_MESSAGE_SIZE:
            raise ValidationError("Message too large")

        cls._reject_bad_text(message, "message")

        payload = envelope.get("payload", {})
        if payload not in ({}, None):
            raise ValidationError("send-chat-message payload must be empty")

    @classmethod
    def _validate_run_command(cls, envelope: dict[str, Any]) -> None:
        payload = envelope.get("payload")
        if not isinstance(payload, dict):
            raise ValidationError("payload must be dict")

        if envelope.get("target_chat_id") != "gateway-brain-supervisor":
            raise ValidationError("Invalid target_chat_id for run-command")

        if envelope.get("delivery_kind") != "local_capability":
            raise ValidationError("Invalid delivery_kind for run-command")

        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not cwd.strip():
            raise ValidationError("Missing payload.cwd")
        cls._reject_bad_text(cwd, "payload.cwd")

        timeout_seconds = payload.get("timeout_seconds")
        if not isinstance(timeout_seconds, int):
            raise ValidationError("payload.timeout_seconds must be int")
        if timeout_seconds <= 0 or timeout_seconds > cls.MAX_TIMEOUT_SECONDS:
            raise ValidationError("payload.timeout_seconds out of range")

        command = payload.get("command")
        if not isinstance(command, list) or not command:
            raise ValidationError("payload.command must be non-empty list")
        if len(command) > cls.MAX_COMMAND_PARTS:
            raise ValidationError("payload.command has too many parts")

        for index, part in enumerate(command):
            if not isinstance(part, str) or not part:
                raise ValidationError(f"payload.command[{index}] must be non-empty string")
            if len(part) > cls.MAX_COMMAND_PART_SIZE:
                raise ValidationError(f"payload.command[{index}] too large")
            cls._reject_bad_text(part, f"payload.command[{index}]")

    @classmethod
    def _reject_bad_text(cls, value: str, field: str) -> None:
        if value.strip() in cls.FORBIDDEN_PLACEHOLDERS:
            raise ValidationError(f"Forbidden placeholder in {field}")

        for placeholder in cls.FORBIDDEN_PLACEHOLDERS:
            if placeholder in value:
                raise ValidationError(f"Forbidden placeholder in {field}")

        if any(ch in value for ch in cls.INVISIBLE_CHARS):
            raise ValidationError(f"Invisible character in {field}")

        if "\r" in value:
            raise ValidationError(f"Carriage return in {field}")
