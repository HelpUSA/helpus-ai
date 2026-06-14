from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.command_builder import CommandBuilder
from backend.preflight_validator import PreflightValidator, ValidationError


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_valid(envelope: dict) -> None:
    assert_true(PreflightValidator.validate(envelope) is True, "expected valid envelope")


def assert_invalid(envelope: dict, marker: str) -> None:
    try:
        PreflightValidator.validate(envelope)
    except ValidationError as exc:
        assert_true(marker in str(exc), f"expected {marker!r} in {exc!r}")
        return
    raise AssertionError("expected invalid envelope")


def main() -> None:
    source_chat_id = "source-chat-id"

    send_chat = CommandBuilder.build_send_chat(
        source_chat_id=source_chat_id,
        target_chat_id="target-chat-id",
        message="hello watcher",
        conversation_id="smoke_watcher_envelope_builder",
        from_agent="HelpUS AI smoke",
        command_id="send_chat_smoke_001",
    )
    assert_true(send_chat["action"] == "send-chat-message", "send action mismatch")
    assert_true(send_chat["delivery_kind"] == "inter_agent_message", "send delivery mismatch")
    assert_true(send_chat["payload"] == {}, "send payload should be empty")
    assert_true(send_chat["message"] == "hello watcher", "send message mismatch")
    assert_valid(send_chat)

    run_command = CommandBuilder.build_run_command(
        source_chat_id=source_chat_id,
        cwd="D:/dev/ai",
        command=["powershell", "-NoProfile", "-Command", "git status -sb"],
        conversation_id="smoke_watcher_envelope_builder",
        from_agent="HelpUS AI smoke",
        timeout_seconds=120,
        command_id="run_command_smoke_001",
    )
    assert_true(run_command["action"] == "run-command", "run action mismatch")
    assert_true(run_command["target_chat_id"] == CommandBuilder.DEFAULT_LOCAL_TARGET, "run target mismatch")
    assert_true(run_command["delivery_kind"] == "local_capability", "run delivery mismatch")
    assert_true(run_command["payload"]["cwd"] == "D:/dev/ai", "run cwd mismatch")
    assert_true(isinstance(run_command["payload"]["command"], list), "run command must be list")
    assert_valid(run_command)

    generated_a = CommandBuilder.build_run_command(source_chat_id, "D:/dev/ai", ["cmd", "/c", "echo A"])
    generated_b = CommandBuilder.build_run_command(source_chat_id, "D:/dev/ai", ["cmd", "/c", "echo B"])
    assert_true(generated_a["command_id"] != generated_b["command_id"], "command_id should be unique")
    assert_true(generated_a["command_id"].startswith("run_command_"), "run command_id prefix mismatch")

    bad_delivery = dict(run_command)
    bad_delivery["delivery_kind"] = "local_inter_agent_message"
    assert_invalid(bad_delivery, "Invalid delivery_kind")

    bad_target = dict(run_command)
    bad_target["target_chat_id"] = "local"
    assert_invalid(bad_target, "Invalid target_chat_id")

    bad_command = dict(run_command)
    bad_command["payload"] = dict(run_command["payload"])
    bad_command["payload"]["command"] = "git status -sb"
    assert_invalid(bad_command, "payload.command must be non-empty list")

    placeholder = CommandBuilder.build_send_chat(
        source_chat_id=source_chat_id,
        target_chat_id="target-chat-id",
        message="{ JSON_VALIDO_AQUI }",
        command_id="send_chat_placeholder_smoke",
    )
    assert_invalid(placeholder, "Forbidden placeholder")

    print("WATCHER_ENVELOPE_BUILDER_SMOKE_OK")


if __name__ == "__main__":
    main()
