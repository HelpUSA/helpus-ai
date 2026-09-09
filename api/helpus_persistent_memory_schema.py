from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Dialect = Literal["sqlite", "postgres"]


SCHEMA_VERSION = "helpus_persistent_memory_v1"


@dataclass(frozen=True)
class MemoryTable:
    name: str
    purpose: str


MEMORY_TABLES = (
    MemoryTable(
        name="helpus_memory_events",
        purpose="Append-only operational conversation and decision events.",
    ),
    MemoryTable(
        name="helpus_memory_feedback",
        purpose="Human or system feedback about prior HelpUSAI behavior.",
    ),
    MemoryTable(
        name="helpus_memory_lessons",
        purpose="Draft lessons extracted from events and feedback.",
    ),
    MemoryTable(
        name="helpus_memory_rules",
        purpose="Human-approved operating rules promoted from lessons.",
    ),
)


def _id_type(dialect: Dialect) -> str:
    if dialect == "postgres":
        return "bigserial primary key"
    return "integer primary key autoincrement"


def _timestamp_default(dialect: Dialect) -> str:
    if dialect == "postgres":
        return "timestamptz not null default now()"
    return "text not null default (datetime('now'))"


def create_schema_sql(dialect: Dialect = "sqlite") -> list[str]:
    if dialect not in ("sqlite", "postgres"):
        raise ValueError(f"Unsupported dialect: {dialect}")

    id_type = _id_type(dialect)
    ts = _timestamp_default(dialect)
    json_type = "jsonb" if dialect == "postgres" else "text"

    statements = [
        f"""
        create table if not exists helpus_memory_events (
            id {id_type},
            created_at {ts},
            event_type text not null,
            source text not null,
            conversation_id text,
            actor text,
            summary text not null,
            details {json_type},
            safety_level text not null default 'normal',
            status text not null default 'recorded'
        )
        """,
        """
        create index if not exists idx_helpus_memory_events_created_at
        on helpus_memory_events (created_at)
        """,
        """
        create index if not exists idx_helpus_memory_events_conversation
        on helpus_memory_events (conversation_id)
        """,
        """
        create index if not exists idx_helpus_memory_events_type
        on helpus_memory_events (event_type)
        """,
        f"""
        create table if not exists helpus_memory_feedback (
            id {id_type},
            created_at {ts},
            event_id integer,
            feedback_type text not null,
            source text not null,
            summary text not null,
            severity text not null default 'info',
            status text not null default 'draft',
            details {json_type}
        )
        """,
        """
        create index if not exists idx_helpus_memory_feedback_status
        on helpus_memory_feedback (status)
        """,
        f"""
        create table if not exists helpus_memory_lessons (
            id {id_type},
            created_at {ts},
            source_feedback_id integer,
            title text not null,
            lesson text not null,
            status text not null default 'draft',
            confidence real not null default 0.0,
            details {json_type}
        )
        """,
        """
        create index if not exists idx_helpus_memory_lessons_status
        on helpus_memory_lessons (status)
        """,
        f"""
        create table if not exists helpus_memory_rules (
            id {id_type},
            created_at {ts},
            source_lesson_id integer,
            rule_key text not null,
            rule_text text not null,
            status text not null default 'draft',
            details {json_type}
        )
        """,
        """
        create unique index if not exists ux_helpus_memory_rules_key_status
        on helpus_memory_rules (rule_key, status)
        """,
    ]

    return [normalize_sql(statement) for statement in statements]


def normalize_sql(statement: str) -> str:
    return "\n".join(line.rstrip() for line in statement.strip().splitlines()) + ";"


def schema_summary() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "tables": [{"name": table.name, "purpose": table.purpose} for table in MEMORY_TABLES],
        "safety": {
            "append_only_events": True,
            "feedback_defaults_to_draft": True,
            "lessons_default_to_draft": True,
            "rules_default_to_draft": True,
            "automatic_rule_promotion": False,
        },
    }
