from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

try:
    from helpus_internal_memory_recorder import get_database_url
except ImportError:
    from backend.helpus_internal_memory_recorder import get_database_url

MEMORY_CONTEXT_ENABLED_ENV = "HELPUS_MEMORY_CONTEXT_ENABLED"
DEFAULT_MEMORY_READ_LIMIT = 8
MAX_EVENT_SUMMARY_LENGTH = 500


@dataclass(frozen=True)
class MemoryEvent:
    id: int
    created_at: str
    event_type: str
    source: str
    conversation_id: str | None
    actor: str | None
    summary: str
    details: dict[str, Any]
    safety_level: str
    status: str


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def memory_context_enabled() -> bool:
    return _truthy(os.getenv(MEMORY_CONTEXT_ENABLED_ENV))


def _connect(database_url: str):
    try:
        import psycopg

        return "psycopg", psycopg.connect(database_url, connect_timeout=10)
    except Exception:
        import psycopg2

        return "psycopg2", psycopg2.connect(database_url, connect_timeout=10)


def compact_summary(value: Any, limit: int = MAX_EVENT_SUMMARY_LENGTH) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    text = " ".join(part for part in text.split() if part)

    if len(text) <= limit:
        return text

    suffix = "...[truncated]"
    return text[: max(0, limit - len(suffix))].rstrip() + suffix


def _parse_details(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if value is None:
        return {}

    try:
        return json.loads(str(value))
    except Exception:
        return {}


def _row_to_event(row: Any) -> MemoryEvent:
    return MemoryEvent(
        id=int(row[0]),
        created_at=str(row[1]),
        event_type=str(row[2] or ""),
        source=str(row[3] or ""),
        conversation_id=row[4],
        actor=row[5],
        summary=compact_summary(row[6]),
        details=_parse_details(row[7]),
        safety_level=str(row[8] or ""),
        status=str(row[9] or ""),
    )


def read_recent_memory_events(
    *,
    conversation_id: str | None = None,
    project_id: str | None = None,
    limit: int = DEFAULT_MEMORY_READ_LIMIT,
) -> list[MemoryEvent]:
    if not memory_context_enabled():
        return []

    _, database_url = get_database_url()
    if not database_url:
        return []

    safe_limit = max(1, min(int(limit or DEFAULT_MEMORY_READ_LIMIT), 20))

    where = [
        "source = 'helpus_chat_runtime'",
        "status = 'recorded'",
        "safety_level in ('normal', 'low', '')",
    ]
    params: list[Any] = []

    if conversation_id and project_id:
        where.append("(conversation_id = %s or details->>'project_id' = %s)")
        params.extend([conversation_id, project_id])
    elif conversation_id:
        where.append("conversation_id = %s")
        params.append(conversation_id)
    elif project_id:
        where.append("details->>'project_id' = %s")
        params.append(project_id)

    params.append(safe_limit)

    sql = f"""
        select
            id,
            created_at,
            event_type,
            source,
            conversation_id,
            actor,
            summary,
            details::text,
            safety_level,
            status
        from helpus_memory_events
        where {" and ".join(where)}
        order by id desc
        limit %s
    """

    try:
        _, conn = _connect(database_url)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
        finally:
            conn.close()
    except Exception:
        return []

    return [_row_to_event(row) for row in rows]


def read_memory_reader_status() -> dict[str, Any]:
    db_key, database_url = get_database_url()

    return {
        "enabled": memory_context_enabled(),
        "enabled_env": MEMORY_CONTEXT_ENABLED_ENV,
        "database_url_present": bool(database_url),
        "database_url_key": db_key or None,
        "default_limit": DEFAULT_MEMORY_READ_LIMIT,
        "automatic_feedback_promotion": False,
        "automatic_lesson_promotion": False,
        "automatic_rule_promotion": False,
    }
