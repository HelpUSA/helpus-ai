from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from evolving_memory_schema import apply_schema, connect_memory_db

def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    names = [description[0] for description in cursor.description]
    return dict(zip(names, row))

def _fetch_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

def _fetch_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = conn.execute(sql, params)
    return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

class EvolvingMemoryReport:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self.conn = connect_memory_db(self.db_path)
        apply_schema(self.conn)

    def close(self) -> None:
        self.conn.close()

    def snapshot(self, *, project_id: str = "helpus-ai", limit: int = 20) -> dict[str, Any]:
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        counts = {
            "experience_events": _fetch_count(self.conn, "experience_events"),
            "command_requests": _fetch_count(self.conn, "command_requests"),
            "command_results": _fetch_count(self.conn, "command_results"),
            "lessons": _fetch_count(self.conn, "lessons"),
            "rules": _fetch_count(self.conn, "rules"),
            "evaluations": _fetch_count(self.conn, "evaluations"),
        }
        rules = _fetch_rows(self.conn, "SELECT id, scope, name, priority, enabled, status, updated_at FROM rules ORDER BY priority DESC, updated_at DESC, id DESC LIMIT ?", (limit,))
        lessons = _fetch_rows(self.conn, "SELECT id, project_id, root_cause, severity, status, created_at FROM lessons WHERE project_id = ? ORDER BY created_at DESC, id DESC LIMIT ?", (project_id, limit))
        evaluations = _fetch_rows(self.conn, "SELECT id, project_id, name, kind, target, status, created_at FROM evaluations WHERE project_id = ? ORDER BY created_at DESC, id DESC LIMIT ?", (project_id, limit))
        commands = _fetch_rows(self.conn, "SELECT id, command_id, project_id, cwd, risk_level, status, created_at FROM command_requests WHERE project_id = ? ORDER BY created_at DESC, id DESC LIMIT ?", (project_id, limit))
        failures = _fetch_rows(self.conn, "SELECT cr.id, cr.command_request_id, cr.return_code, cr.summary, cr.created_at FROM command_results cr WHERE cr.return_code != 0 ORDER BY cr.created_at DESC, cr.id DESC LIMIT ?", (limit,))
        return {"project_id": project_id, "counts": counts, "rules": rules, "lessons": lessons, "evaluations": evaluations, "command_requests": commands, "failed_command_results": failures}

    def render_markdown(self, *, project_id: str = "helpus-ai", limit: int = 20) -> str:
        data = self.snapshot(project_id=project_id, limit=limit)
        lines: list[str] = []
        lines.append(f"# Evolving Memory Report: {project_id}")
        lines.append("")
        lines.append("## Counts")
        for key, value in sorted(data["counts"].items()):
            lines.append(f"- {key}: {value}")
        lines.append("")
        for section in ("rules", "lessons", "evaluations", "command_requests", "failed_command_results"):
            lines.append(f"## {section}")
            rows = data[section]
            if not rows:
                lines.append("- none")
            for row in rows:
                label = row.get("name") or row.get("command_id") or row.get("root_cause") or row.get("id")
                status = row.get("status") or row.get("return_code") or ""
                lines.append(f"- {row.get('id')}: {label} {status}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def export_json(self, *, project_id: str = "helpus-ai", limit: int = 20) -> str:
        return json.dumps(self.snapshot(project_id=project_id, limit=limit), ensure_ascii=False, indent=2, sort_keys=True)
