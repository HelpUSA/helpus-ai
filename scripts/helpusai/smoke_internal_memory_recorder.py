from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend import helpus_internal_memory_recorder as rec


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    old_env = dict(os.environ)

    try:
        os.environ.pop(rec.MEMORY_RECORDING_ENABLED_ENV, None)
        for key in ("DATABASE_URL", "POSTGRES_URL", "DATABASE_PUBLIC_URL"):
            os.environ.pop(key, None)

        check(
            rec.memory_recording_enabled() is False,
            "recording should be disabled by default",
        )

        disabled = rec.record_chat_memory_event(
            user_message="hello",
            assistant_reply="hi",
            conversation_id="conv-1",
            provider="deepseek",
            project_id="general",
        )
        check(disabled.status == "skipped", "disabled status mismatch")
        check(disabled.enabled is False, "disabled enabled mismatch")
        check(disabled.reason == "recording_disabled", "disabled reason mismatch")

        os.environ[rec.MEMORY_RECORDING_ENABLED_ENV] = "1"
        check(
            rec.memory_recording_enabled() is True,
            "recording should be enabled with env=1",
        )

        missing_db = rec.record_chat_memory_event(
            user_message="hello",
            assistant_reply="hi",
            conversation_id="conv-1",
            provider="deepseek",
            project_id="general",
        )
        check(missing_db.status == "skipped", "missing db status mismatch")
        check(missing_db.enabled is True, "missing db enabled mismatch")
        check(missing_db.reason == "database_url_missing", "missing db reason mismatch")

        summary = rec.build_event_summary("a" * 1000, "b" * 1000)
        check(len(summary) <= rec.MAX_SUMMARY_LENGTH, "summary too long")

        details = rec.build_event_details(
            user_message="question",
            assistant_reply="answer",
            conversation_id="conv-2",
            provider="deepseek",
            route="chat",
            project_id="general",
            extra={"sample": True},
        )
        check(details["conversation_id"] == "conv-2", "conversation id missing")
        check(details["provider"] == "deepseek", "provider missing")
        check(details["project_id"] == "general", "project missing")
        check(
            details["automatic_feedback_promotion"] is False,
            "unsafe feedback promotion",
        )
        check(
            details["automatic_lesson_promotion"] is False,
            "unsafe lesson promotion",
        )
        check(
            details["automatic_rule_promotion"] is False,
            "unsafe rule promotion",
        )

        masked = rec.mask_database_url(
            "postgresql://user:secret@example.com:5432/railway"
        )
        check("secret" not in masked, "secret leaked")
        check("user:" not in masked, "username leaked")
        check("example.com" in masked, "host missing")

        safe = rec.safe_record_chat_memory_event(
            user_message="hello",
            assistant_reply="hi",
            conversation_id="conv-3",
        )
        check(safe.status in {"skipped", "recorded"}, "safe status invalid")

        status = rec.recorder_status()
        check(status["enabled"] is True, "status enabled mismatch")
        check(status["source"] == rec.MEMORY_RECORDING_SOURCE, "source mismatch")
        check(
            status["automatic_feedback_promotion"] is False,
            "status unsafe feedback promotion",
        )
        check(
            status["automatic_lesson_promotion"] is False,
            "status unsafe lesson promotion",
        )
        check(
            status["automatic_rule_promotion"] is False,
            "status unsafe rule promotion",
        )

    finally:
        os.environ.clear()
        os.environ.update(old_env)

    print("OK smoke_internal_memory_recorder")


if __name__ == "__main__":
    main()
