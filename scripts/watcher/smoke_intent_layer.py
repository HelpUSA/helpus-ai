import sys

sys.path.insert(0, "backend")

from intent_layer import IntentLayer
from preflight_validator import PreflightValidator, ValidationError


def expect_validation_error(label, envelope):
    try:
        PreflightValidator.validate(envelope)
    except ValidationError:
        print(f"EXPECTED_FAIL {label}")
        return
    raise AssertionError(f"Expected validation failure: {label}")


send_envelope = IntentLayer.build(
    {
        "type": "send_chat",
        "source_chat_id": "src",
        "target_chat_id": "dst",
        "message": "ACK",
        "conversation_id": "conv",
        "from_agent": "agent",
    }
)
assert send_envelope["action"] == "send-chat-message"
assert send_envelope["delivery_kind"] == "inter_agent_message"
assert send_envelope["message"] == "ACK"

run_envelope = IntentLayer.build(
    {
        "type": "run_command",
        "source_chat_id": "src",
        "cwd": "D:/dev/ai",
        "command": ["git", "status", "-sb"],
        "conversation_id": "conv",
        "from_agent": "agent",
        "timeout_seconds": 30,
    }
)
assert run_envelope["action"] == "run-command"
assert run_envelope["target_chat_id"] == "gateway-brain-supervisor"
assert run_envelope["delivery_kind"] == "local_capability"

bad_delivery = dict(send_envelope)
bad_delivery["delivery_kind"] = "local_inter_agent_message"
expect_validation_error("old_delivery_kind", bad_delivery)

bad_target = dict(run_envelope)
bad_target["target_chat_id"] = "local"
expect_validation_error("local_target", bad_target)

bad_placeholder = dict(send_envelope)
bad_placeholder["message"] = "{ JSON PURO }"
expect_validation_error("placeholder", bad_placeholder)

bad_command = dict(run_envelope)
bad_command["payload"] = dict(run_envelope["payload"])
bad_command["payload"]["command"] = "git status -sb"
expect_validation_error("command_not_list", bad_command)

print("INTENT_LAYER_SMOKE_OK")
