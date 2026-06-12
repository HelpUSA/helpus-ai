import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from command_builder import CommandBuilder
from intent_layer import IntentLayer
from preflight_validator import PreflightValidator, ValidationError


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_validation_error(label, envelope):
    try:
        PreflightValidator.validate(envelope)
    except ValidationError:
        print(f"EXPECTED_FAIL {label}")
        return
    raise AssertionError(f"Expected validation failure: {label}")


def test_builder_send_chat():
    envelope = CommandBuilder.build_send_chat(
        source_chat_id="source-chat",
        target_chat_id="target-chat",
        message="ACK behavior smoke",
        conversation_id="behavior-smoke",
        from_agent="HelpUS AI",
        command_id="send_chat_behavior_smoke",
    )
    PreflightValidator.validate(envelope)
    assert_true(envelope["action"] == "send-chat-message", "send-chat action mismatch")
    assert_true(envelope["delivery_kind"] == "inter_agent_message", "send-chat delivery mismatch")
    assert_true(envelope["message"] == "ACK behavior smoke", "message must be top-level")
    assert_true(envelope["payload"] == {}, "send-chat payload must be empty")


def test_builder_run_command():
    envelope = CommandBuilder.build_run_command(
        source_chat_id="source-chat",
        cwd="D:/dev/ai",
        command=["git", "status", "-sb"],
        conversation_id="behavior-smoke",
        from_agent="HelpUS AI",
        timeout_seconds=30,
        command_id="run_command_behavior_smoke",
    )
    PreflightValidator.validate(envelope)
    assert_true(envelope["action"] == "run-command", "run-command action mismatch")
    assert_true(envelope["target_chat_id"] == "gateway-brain-supervisor", "run target mismatch")
    assert_true(envelope["delivery_kind"] == "local_capability", "run delivery mismatch")
    assert_true(envelope["payload"]["command"] == ["git", "status", "-sb"], "command list mismatch")


def test_intent_layer():
    send_envelope = IntentLayer.build(
        {
            "type": "send_chat",
            "source_chat_id": "source-chat",
            "target_chat_id": "target-chat",
            "message": "ACK intent smoke",
            "conversation_id": "behavior-smoke",
            "from_agent": "HelpUS AI",
        }
    )
    run_envelope = IntentLayer.build(
        {
            "type": "run_command",
            "source_chat_id": "source-chat",
            "cwd": "D:/dev/ai",
            "command": ["git", "status", "-sb"],
            "conversation_id": "behavior-smoke",
            "from_agent": "HelpUS AI",
            "timeout_seconds": 30,
        }
    )
    PreflightValidator.validate(send_envelope)
    PreflightValidator.validate(run_envelope)


def test_negative_cases():
    valid_send = CommandBuilder.build_send_chat("src", "dst", "ACK", "conv", "agent")
    valid_run = CommandBuilder.build_run_command("src", "D:/dev/ai", ["git", "status", "-sb"], "conv", "agent")

    old_delivery = dict(valid_send)
    old_delivery["delivery_kind"] = "local_inter_agent_message"
    expect_validation_error("old_delivery_kind", old_delivery)

    local_target = dict(valid_run)
    local_target["target_chat_id"] = "local"
    expect_validation_error("local_target", local_target)

    placeholder = dict(valid_send)
    placeholder["message"] = "{ JSON PURO }"
    expect_validation_error("placeholder", placeholder)

    command_not_list = dict(valid_run)
    command_not_list["payload"] = dict(valid_run["payload"])
    command_not_list["payload"]["command"] = "git status -sb"
    expect_validation_error("command_not_list", command_not_list)

    missing_message = dict(valid_send)
    missing_message["message"] = ""
    expect_validation_error("missing_message", missing_message)


def test_cerebro_prompt_contract():
    prompt_file = BACKEND / "cerebro.py"
    text = prompt_file.read_text(encoding="utf-8")
    required = [
        "Nunca simule recibos",
        "send-chat-message",
        "run-command",
        "JSON estrito",
        "intent: send_chat ou run_command",
        "builder, validator e envelope valido",
    ]
    for marker in required:
        assert_true(marker in text, f"missing prompt marker: {marker}")


def main():
    test_builder_send_chat()
    test_builder_run_command()
    test_intent_layer()
    test_negative_cases()
    test_cerebro_prompt_contract()
    print("BEHAVIOR_SMOKE_OK")


if __name__ == "__main__":
    main()
