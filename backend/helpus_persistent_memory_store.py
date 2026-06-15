from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from backend.helpus_persistent_memory_schema import SCHEMA_VERSION, create_schema_sql


@dataclass(frozen=True)
class PersistentMemoryStatus:
    schema_version: str
    event_count: int
    feedback_count: int
    lesson_count: int
    rule_count: int


class PersistentMemoryStore:
    """Small guarded memory store.

    The first implementation is intentionally sqlite-backed for local smokes.
    Production Postgres application is a separate, explicit migration step.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            for statement in create_schema_sql("sqlite"):
                conn.execute(statement)

    def record_event(
        self,
        *,
        event_type: str,
        source: str,
        summary: str,
        conversation_id: str | None = None,
        actor: str | None = None,
        details: dict[str, Any] | None = None,
        safety_level: str = "normal",
        status: str = "recorded",
    ) -> int:
        if not event_type.strip():
            raise ValueError("event_type is required")
        if not source.strip():
            raise ValueError("source is required")
        if not summary.strip():
            raise ValueError("summary is required")

        self.initialize()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                insert into helpus_memory_events (
                    event_type, source, conversation_id, actor, summary, details, safety_level, status
                )
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_type,
                    source,
                    conversation_id,
                    actor,
                    summary,
                    json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
                    safety_level,
                    status,
                ),
            )
            return int(cursor.lastrowid)

    def record_feedback(
        self,
        *,
        feedback_type: str,
        source: str,
        summary: str,
        event_id: int | None = None,
        severity: str = "info",
        status: str = "draft",
        details: dict[str, Any] | None = None,
    ) -> int:
        if status != "draft":
            raise ValueError("feedback must start as draft")
        if not feedback_type.strip():
            raise ValueError("feedback_type is required")
        if not source.strip():
            raise ValueError("source is required")
        if not summary.strip():
            raise ValueError("summary is required")

        self.initialize()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                insert into helpus_memory_feedback (
                    event_id, feedback_type, source, summary, severity, status, details
                )
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    feedback_type,
                    source,
                    summary,
                    severity,
                    status,
                    json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
                ),
            )
            return int(cursor.lastrowid)

    def list_recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        self.initialize()
        with self.connection() as conn:
            rows = conn.execute(
                """
                select id, created_at, event_type, source, conversation_id, actor,
                       summary, details, safety_level, status
                from helpus_memory_events
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def list_draft_feedback(self, limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")

        self.initialize()
        with self.connection() as conn:
            rows = conn.execute(
                """
                select id, created_at, event_id, feedback_type, source,
                       summary, severity, status, details
                from helpus_memory_feedback
                where status = 'draft'
                order by id desc
                limit ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def status(self) -> PersistentMemoryStatus:
        self.initialize()
        with self.connection() as conn:
            return PersistentMemoryStatus(
                schema_version=SCHEMA_VERSION,
                event_count=self._count(conn, "helpus_memory_events"),
                feedback_count=self._count(conn, "helpus_memory_feedback"),
                lesson_count=self._count(conn, "helpus_memory_lessons"),
                rule_count=self._count(conn, "helpus_memory_rules"),
            )

    def status_dict(self) -> dict[str, Any]:
        status = self.status()
        return {
            "schema_version": status.schema_version,
            "event_count": status.event_count,
            "feedback_count": status.feedback_count,
            "lesson_count": status.lesson_count,
            "rule_count": status.rule_count,
            "ready_for_production_migration": False,
            "writes_enabled": "local_store_only",
        }

    @staticmethod
    def _count(conn: sqlite3.Connection, table: str) -> int:
        row = conn.execute(f"select count(*) as count from {table}").fetchone()
        return int(row["count"])

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        item = dict(row)
        if isinstance(item.get("details"), str) and item["details"]:
            try:
                item["details"] = json.loads(item["details"])
            except json.JSONDecodeError:
                item["details"] = {"raw": item["details"]}
        return item
