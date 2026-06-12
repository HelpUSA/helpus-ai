import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "backend"))

from command_builder import CommandBuilder
from intent_layer import IntentLayer
from preflight_validator import PreflightValidator, ValidationError


def expect_fail(label, envelope):
    try:
        PreflightValidator.validate(envelope)
    except ValidationError:
        print(f"EXPECTED_FAIL {label}")
        return
    raise AssertionError(f"Expected validation failure: {label}")


for i in range(30):
    send_env = IntentLayer.build(
        {
            "type": "send_chat",
            "source_chat_id": f"src-{i}",
            "target_chat_id": f"dst-{i}",
            "message": f"ACK stress {i}",
            "conversation_id": "stress",
            "from_agent": "HelpUS AI",
        }
    )
    run_env = IntentLayer.build(
        {
            "type": "run_command",
            "source_chat_id": f"src-{i}",
            "cwd": "D:/dev/ai",
            "command": ["git", "status", "-sb"],
            "conversation_id": "stress",
            "from_agent": "HelpUS AI",
            "timeout_seconds": 30,
        }
    )
    assert PreflightValidator.validate(send_env) is True
    assert PreflightValidator.validate(run_env) is True


placeholder = CommandBuilder.build_send_chat("src", "dst", "{ JSON PURO }", "conv", "agent")
expect_fail("placeholder", placeholder)

bad_timeout = CommandBuilder.build_run_command(
    "src",
    "D:/dev/ai",
    ["git", "status"],
    "conv",
    "agent",
    timeout_seconds=99999,
)
expect_fail("timeout_range", bad_timeout)

empty_command = CommandBuilder.build_run_command(
    "src",
    "D:/dev/ai",
    ["git", ""],
    "conv",
    "agent",
)
expect_fail("empty_command_part", empty_command)

print("WATCHER_STRESS_SMOKE_OK")
