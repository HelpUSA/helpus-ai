from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from evolving_memory_schema import apply_schema, connect_memory_db


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    names = [description[0] for description in cursor.description]
    return dict(zip(names, row))


class EvolvingCommandStore:
    # Append/read store for HelpUSAI command_requests and command_results.

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self.conn = connect_memory_db(self.db_path)
        apply_schema(self.conn)

    def close(self) -> None:
        self.conn.close()

    def record_command_request(self, *, command_id: str, project_id: str, cwd: str, command_json: Any, reason: str, risk_level: str = "low", requested_by_agent_id: str | None = None, requires_confirmation: bool = True, request_id: str | None = None) -> dict[str, Any]:
        if risk_level not in {"low", "medium", "high"}:
            raise ValueError("invalid risk_level")
        new_id = request_id or f"req-{uuid.uuid4()}"
        sql = "INSERT INTO command_requests (id, command_id, requested_by_agent_id, project_id, cwd, command_json, reason, risk_level, requires_confirmation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self.conn.execute(sql, (new_id, command_id, requested_by_agent_id, project_id, cwd, _json_dumps(command_json), reason, risk_level, 1 if requires_confirmation else 0))
        self.conn.commit()
        return self.get_command_request(new_id)

    def get_command_request(self, request_id: str) -> dict[str, Any]:
        sql = "SELECT id, command_id, requested_by_agent_id, project_id, cwd, command_json, reason, risk_level, status, requires_confirmation, created_at, approved_at, started_at, finished_at FROM command_requests WHERE id = ?"
        cursor = self.conn.execute(sql, (request_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(request_id)
        return _row_to_dict(cursor, row)

    def get_command_request_by_command_id(self, command_id: str) -> dict[str, Any]:
        sql = "SELECT id, command_id, requested_by_agent_id, project_id, cwd, command_json, reason, risk_level, status, requires_confirmation, created_at, approved_at, started_at, finished_at FROM command_requests WHERE command_id = ?"
        cursor = self.conn.execute(sql, (command_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(command_id)
        return _row_to_dict(cursor, row)

    def list_command_requests(self, *, project_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        if project_id is None:
            sql = "SELECT id, command_id, project_id, cwd, command_json, reason, risk_level, status, requires_confirmation, created_at FROM command_requests ORDER BY created_at DESC, id DESC LIMIT ?"
            cursor = self.conn.execute(sql, (limit,))
        else:
            sql = "SELECT id, command_id, project_id, cwd, command_json, reason, risk_level, status, requires_confirmation, created_at FROM command_requests WHERE project_id = ? ORDER BY created_at DESC, id DESC LIMIT ?"
            cursor = self.conn.execute(sql, (project_id, limit))
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]

    def record_command_result(self, *, command_request_id: str, return_code: int, stdout: str = "", stderr: str = "", files_changed_json: Any = None, diff_stat: str = "", summary: str | None = None, result_id: str | None = None) -> dict[str, Any]:
        new_id = result_id or f"res-{uuid.uuid4()}"
        files_changed = files_changed_json if files_changed_json is not None else []
        sql = "INSERT INTO command_results (id, command_request_id, return_code, stdout, stderr, files_changed_json, diff_stat, summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        self.conn.execute(sql, (new_id, command_request_id, return_code, stdout, stderr, _json_dumps(files_changed), diff_stat, summary))
        self.conn.commit()
        return self.get_command_result(new_id)

    def get_command_result(self, result_id: str) -> dict[str, Any]:
        sql = "SELECT id, command_request_id, return_code, stdout, stderr, files_changed_json, diff_stat, summary, created_at FROM command_results WHERE id = ?"
        cursor = self.conn.execute(sql, (result_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(result_id)
        return _row_to_dict(cursor, row)

    def list_command_results_for_request(self, command_request_id: str) -> list[dict[str, Any]]:
        sql = "SELECT id, command_request_id, return_code, stdout, stderr, files_changed_json, diff_stat, summary, created_at FROM command_results WHERE command_request_id = ? ORDER BY created_at DESC, id DESC"
        cursor = self.conn.execute(sql, (command_request_id,))
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
