from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.command_builder import CommandBuilder
from backend.preflight_validator import PreflightValidator


SOURCE_CHAT_ID = "6a2ebfa8-9a0c-83e9-9019-263ee430e1b1"


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def build(index: int) -> dict:
    return CommandBuilder.build_run_command(
        source_chat_id=SOURCE_CHAT_ID,
        cwd="D:/dev/ai",
        command=["cmd", "/c", "echo", "unique", str(index)],
        conversation_id="helpus_command_id_uniqueness_smoke",
        from_agent="HelpUS AI smoke",
        timeout_seconds=60,
    )


def main() -> None:
    envelopes = [build(index) for index in range(25)]
    command_ids = [envelope["command_id"] for envelope in envelopes]

    assert_true(len(command_ids) == len(set(command_ids)), "command_id values must be unique")
    assert_true(all(command_ids), "command_id values must be non-empty")
    assert_true(all(isinstance(value, str) for value in command_ids), "command_id values must be strings")
    assert_true(all(len(value) >= 12 for value in command_ids), "command_id values must be descriptive enough")

    for envelope in envelopes:
        PreflightValidator.validate(envelope)
        assert_true(envelope["action"] == "run-command", "action must be run-command")
        assert_true(envelope["delivery_kind"] == "local_capability", "delivery_kind must be local_capability")
        assert_true(envelope["payload"]["cwd"] == "D:/dev/ai", "cwd must be preserved")
        assert_true(isinstance(envelope["payload"]["command"], list), "command must remain a list")

    print("COMMAND_ID_UNIQUENESS_SMOKE_OK")


if __name__ == "__main__":
    main()
