from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.chat_watcher_orchestrator import build_status_message, orchestrate_chat_watcher

SOURCE_CHAT_ID = "6a2ebfa8-9a0c-83e9-9019-263ee430e1b1"


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def assert_valid_run_envelope(envelope):
    assert_true(isinstance(envelope, dict), "envelope must be dict")
    assert_equal(envelope["action"], "run-command", "action")
    assert_equal(envelope["delivery_kind"], "local_capability", "delivery_kind")
    assert_equal(envelope["target_chat_id"], "gateway-brain-supervisor", "target")
    assert_equal(envelope["payload"]["cwd"], "D:/dev/ai", "cwd")
    assert_true(isinstance(envelope["payload"]["command"], list), "command list")


def main() -> None:
    parse = orchestrate_chat_watcher("[AI_LOCAL_ERRO] tipo=envelope_parse_error", SOURCE_CHAT_ID)
    assert_equal(parse["category"], "recover", "parse category")
    assert_equal(parse["action"], "inspect_recovery", "parse action")
    assert_equal(parse["recovery"]["category"], "envelope_parse_error", "parse recovery")
    assert_valid_run_envelope(parse["envelope"])
    assert_true(parse["envelope"]["command_id"].startswith("recover_"), "recover command prefix")

    failed = orchestrate_chat_watcher("[AI_LOCAL_RUN] status=failed return_code=1", SOURCE_CHAT_ID)
    assert_equal(failed["category"], "recover", "failed category")
    assert_equal(failed["recovery"]["risk"], "partial_change_possible", "failed risk")
    assert_valid_run_envelope(failed["envelope"])

    success = orchestrate_chat_watcher("[AI_LOCAL_RUN] status=acked return_code=0", SOURCE_CHAT_ID)
    assert_equal(success["category"], "result", "success category")
    assert_equal(success["action"], "summarize_result", "success action")
    assert_equal(success["envelope"], None, "success envelope")

    sensitive = orchestrate_chat_watcher("deploy production agora", SOURCE_CHAT_ID)
    assert_equal(sensitive["category"], "stop", "sensitive category")
    assert_equal(sensitive["should_stop"], True, "sensitive stop")
    assert_equal(sensitive["envelope"], None, "sensitive envelope")

    inspect = orchestrate_chat_watcher("inspecione o repo", SOURCE_CHAT_ID)
    assert_equal(inspect["category"], "inspect", "inspect category")
    assert_valid_run_envelope(inspect["envelope"])

    validate = orchestrate_chat_watcher("valide smoke e build", SOURCE_CHAT_ID)
    assert_equal(validate["category"], "validate", "validate category")
    assert_equal(validate["action"], "validate_suite", "validate action")
    assert_valid_run_envelope(validate["envelope"])

    message = build_status_message(validate)
    assert_true("Status HelpUS AI:" in message, "status prefix")
    assert_true("validate_suite" in message, "status action")

    print("CHAT_WATCHER_ORCHESTRATOR_SMOKE_OK")


if __name__ == "__main__":
    main()
