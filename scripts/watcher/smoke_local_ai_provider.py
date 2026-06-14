from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.local_ai_provider import (
    build_local_ai_analysis_request,
    export_local_ai_config,
    is_local_ai_available,
    load_local_ai_config,
    render_local_ai_summary,
)


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    disabled_env = {}
    disabled_config = load_local_ai_config(disabled_env)
    assert_equal(disabled_config.enabled, False, "default enabled")
    assert_equal(is_local_ai_available(disabled_config), False, "default available")

    disabled_request = build_local_ai_analysis_request("analyze repo", disabled_config)
    assert_equal(disabled_request["enabled"], False, "disabled request enabled")
    assert_equal(disabled_request["mode"], "analysis_only", "disabled mode")
    assert_equal(disabled_request["can_execute_commands"], False, "disabled commands")
    assert_equal(disabled_request["request"], None, "disabled request payload")

    enabled_env = {
        "HELPUS_LOCAL_AI_ENABLED": "true",
        "HELPUS_LOCAL_AI_BASE_URL": "http://127.0.0.1:11434/",
        "HELPUS_LOCAL_AI_MODEL": "llama-test",
        "HELPUS_LOCAL_AI_TIMEOUT_SECONDS": "7",
    }
    enabled_config = load_local_ai_config(enabled_env)
    assert_equal(enabled_config.enabled, True, "enabled flag")
    assert_equal(enabled_config.base_url, "http://127.0.0.1:11434", "base url trim")
    assert_equal(enabled_config.model, "llama-test", "model")
    assert_equal(enabled_config.timeout_seconds, 7.0, "timeout")
    assert_equal(is_local_ai_available(enabled_config), True, "enabled available")

    enabled_request = build_local_ai_analysis_request("study HelpUS AI", enabled_config)
    assert_equal(enabled_request["enabled"], True, "enabled request")
    assert_equal(enabled_request["provider"], "local_ai", "provider")
    assert_equal(enabled_request["mode"], "analysis_only", "mode")
    assert_equal(enabled_request["can_execute_commands"], False, "commands disabled")
    assert_equal(enabled_request["request"]["method"], "POST", "method")
    assert_true(enabled_request["request"]["url"].endswith("/v1/chat/completions"), "url path")
    assert_equal(enabled_request["request"]["json"]["model"], "llama-test", "json model")
    assert_true("Never execute commands" in enabled_request["request"]["json"]["messages"][0]["content"], "system guardrail")

    bad_timeout = load_local_ai_config({"HELPUS_LOCAL_AI_ENABLED": "1", "HELPUS_LOCAL_AI_TIMEOUT_SECONDS": "999"})
    assert_equal(bad_timeout.timeout_seconds, 15.0, "bad timeout default")

    summary = render_local_ai_summary(enabled_config)
    assert_true("local_ai_status=enabled" in summary, "summary enabled")
    assert_true("mode=analysis_only" in summary, "summary mode")
    assert_true("can_execute_commands=False" in summary, "summary commands")

    exported = export_local_ai_config(enabled_config)
    assert_equal(exported["model"], "llama-test", "export model")

    source = (ROOT / "backend/local_ai_provider.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "provider must not import subprocess")
    assert_true("os.system" not in source, "provider must not run shell commands")

    try:
        build_local_ai_analysis_request("   ", enabled_config)
    except ValueError:
        pass
    else:
        raise AssertionError("empty prompt should fail")

    print("LOCAL_AI_PROVIDER_SMOKE_OK")


if __name__ == "__main__":
    main()
