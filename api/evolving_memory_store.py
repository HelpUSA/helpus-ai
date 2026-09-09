from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from evolving_memory_schema import apply_schema, connect_memory_db


def _json_dumps(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    names = [description[0] for description in cursor.description]
    return dict(zip(names, row))


class EvolvingMemoryStore:
    """Local persistent store for HelpUSAI evolving memory.

    Micro 2 scope: local append/read persistence only.
    This module does not expose an API, execute commands, call networks, or trigger patches.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self.conn = connect_memory_db(self.db_path)
        apply_schema(self.conn)

    def close(self) -> None:
        self.conn.close()

    def record_experience_event(
        self,
        *,
        project_id: str,
        event_type: str,
        agent_id: str | None = None,
        input_text: str | None = None,
        output_text: str | None = None,
        metadata: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        if not project_id.strip():
            raise ValueError("project_id is required")
        if not event_type.strip():
            raise ValueError("event_type is required")

        new_id = event_id or f"event-{uuid.uuid4()}"
        self.conn.execute(
            """
            INSERT INTO experience_events (
                id, project_id, agent_id, event_type, input_text, output_text, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id,
                project_id,
                agent_id,
                event_type,
                input_text,
                output_text,
                _json_dumps(metadata),
            ),
        )
        self.conn.commit()
        return self.get_experience_event(new_id)

    def get_experience_event(self, event_id: str) -> dict[str, Any]:
        cursor = self.conn.execute(
            """
            SELECT id, project_id, agent_id, event_type, input_text, output_text,
                   metadata_json, created_at
            FROM experience_events
            WHERE id = ?
            """,
            (event_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(event_id)
        return _row_to_dict(cursor, row)

    def list_experience_events(
        self,
        *,
        project_id: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")

        clauses: list[str] = []
        params: list[Any] = []
        if project_id is not None:
            clauses.append("project_id = ?")
            params.append(project_id)
        if event_type is not None:
            clauses.append("event_type = ?")
            params.append(event_type)

        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        cursor = self.conn.execute(
            f"""
            SELECT id, project_id, agent_id, event_type, input_text, output_text,
                   metadata_json, created_at
            FROM experience_events
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (*params, limit),
        )
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

    def count_experience_events(self, *, project_id: str | None = None) -> int:
        if project_id is None:
            return int(self.conn.execute("SELECT COUNT(*) FROM experience_events").fetchone()[0])
        return int(
            self.conn.execute(
                "SELECT COUNT(*) FROM experience_events WHERE project_id = ?",
                (project_id,),
            ).fetchone()[0]
        )
