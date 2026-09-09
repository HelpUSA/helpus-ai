from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

MEMORY_RECORDING_ENABLED_ENV = "HELPUS_MEMORY_RECORDING_ENABLED"
MEMORY_RECORDING_SOURCE = "helpus_chat_runtime"

MAX_SUMMARY_LENGTH = 500
MAX_TEXT_LENGTH = 4000


@dataclass(frozen=True)
class MemoryRecordResult:
    status: str
    enabled: bool
    event_id: int | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def memory_recording_enabled() -> bool:
    return _truthy(os.getenv(MEMORY_RECORDING_ENABLED_ENV))


def compact_text(value: Any, limit: int = MAX_TEXT_LENGTH) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()

    if len(text) <= limit:
        return text

    suffix = "...[truncated]"
    return text[: max(0, limit - len(suffix))].rstrip() + suffix


def build_event_summary(
    user_message: str,
    assistant_reply: str | None = None,
) -> str:
    user_part = compact_text(user_message, 220)
    assistant_part = compact_text(assistant_reply or "", 220)

    if assistant_part:
        return compact_text(
            f"user={user_part} | assistant={assistant_part}",
            MAX_SUMMARY_LENGTH,
        )

    return compact_text(f"user={user_part}", MAX_SUMMARY_LENGTH)


def build_event_details(
    *,
    user_message: str,
    assistant_reply: str | None = None,
    conversation_id: str | None = None,
    provider: str | None = None,
    route: str | None = None,
    project_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "project_id": project_id,
        "provider": provider,
        "route": route,
        "user_message": compact_text(user_message),
        "assistant_reply": compact_text(assistant_reply or ""),
        "extra": extra or {},
        "automatic_feedback_promotion": False,
        "automatic_lesson_promotion": False,
        "automatic_rule_promotion": False,
    }


def mask_database_url(value: str) -> str:
    if not value:
        return ""

    parsed = urlparse(value)
    scheme = parsed.scheme or "postgresql"
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    db = parsed.path or ""

    return f"{scheme}://***:***@{host}{port}{db}"


def get_database_url() -> tuple[str, str]:
    for key in ("DATABASE_URL", "POSTGRES_URL", "DATABASE_PUBLIC_URL"):
        value = os.getenv(key)
        if value:
            return key, value

    return "", ""


def _connect(database_url: str):
    try:
        import psycopg

        return "psycopg", psycopg.connect(database_url, connect_timeout=10)
    except Exception:
        import psycopg2

        return "psycopg2", psycopg2.connect(database_url, connect_timeout=10)


def record_chat_memory_event(
    *,
    user_message: str,
    assistant_reply: str | None = None,
    conversation_id: str | None = None,
    actor: str = "user",
    provider: str | None = None,
    route: str | None = "chat",
    project_id: str | None = None,
    event_type: str = "chat_conversation",
    extra: dict[str, Any] | None = None,
) -> MemoryRecordResult:
    if not memory_recording_enabled():
        return MemoryRecordResult(
            status="skipped",
            enabled=False,
            reason="recording_disabled",
        )

    _, database_url = get_database_url()

    if not database_url:
        return MemoryRecordResult(
            status="skipped",
            enabled=True,
            reason="database_url_missing",
        )

    summary = build_event_summary(user_message, assistant_reply)
    details = build_event_details(
        user_message=user_message,
        assistant_reply=assistant_reply,
        conversation_id=conversation_id,
        provider=provider,
        route=route,
        project_id=project_id,
        extra=extra,
    )

    _, conn = _connect(database_url)

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into helpus_memory_events (
                        event_type,
                        source,
                        conversation_id,
                        actor,
                        summary,
                        details,
                        safety_level,
                        status
                    )
                    values (%s, %s, %s, %s, %s, %s::jsonb, 'normal', 'recorded')
                    returning id
                    """,
                    (
                        event_type,
                        MEMORY_RECORDING_SOURCE,
                        conversation_id,
                        actor,
                        summary,
                        json.dumps(details, ensure_ascii=False, sort_keys=True),
                    ),
                )
                event_id = int(cur.fetchone()[0])
    finally:
        conn.close()

    return MemoryRecordResult(
        status="recorded",
        enabled=True,
        event_id=event_id,
    )


def safe_record_chat_memory_event(**kwargs: Any) -> MemoryRecordResult:
    try:
        return record_chat_memory_event(**kwargs)
    except Exception as exc:
        return MemoryRecordResult(
            status="skipped",
            enabled=memory_recording_enabled(),
            reason=f"recording_error:{type(exc).__name__}",
        )


def recorder_status() -> dict[str, Any]:
    db_key, database_url = get_database_url()

    return {
        "enabled": memory_recording_enabled(),
        "enabled_env": MEMORY_RECORDING_ENABLED_ENV,
        "database_url_key": db_key or None,
        "database_url_masked": mask_database_url(database_url),
        "source": MEMORY_RECORDING_SOURCE,
        "automatic_feedback_promotion": False,
        "automatic_lesson_promotion": False,
        "automatic_rule_promotion": False,
    }
