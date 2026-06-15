from __future__ import annotations

import json
import re
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

def normalize_eval_name(value: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
    return slug or ('evaluation-' + uuid.uuid4().hex[:8])

def command_for_rule(rule_name: str) -> list[str]:
    safe_name = normalize_eval_name(rule_name).replace('-', '_')
    return ['python', 'scripts/watcher/smoke_rule_' + safe_name + '.py']

class EvaluationProposalGenerator:
    def __init__(self, db_path: str | Path = ':memory:') -> None:
        self.db_path = str(db_path)
        self.conn = connect_memory_db(self.db_path)
        apply_schema(self.conn)

    def close(self) -> None:
        self.conn.close()

    def get_rule(self, rule_id: str) -> dict[str, Any]:
        cursor = self.conn.execute('SELECT id, scope, name, rule_text, priority, enabled, status, created_at, updated_at FROM rules WHERE id = ?', (rule_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(rule_id)
        return _row_to_dict(cursor, row)

    def get_evaluation(self, evaluation_id: str) -> dict[str, Any]:
        cursor = self.conn.execute('SELECT id, project_id, name, kind, target, status, command_json, result_json, created_at, updated_at FROM evaluations WHERE id = ?', (evaluation_id,))
        row = cursor.fetchone()
        if row is None:
            raise KeyError(evaluation_id)
        return _row_to_dict(cursor, row)

    def find_evaluation(self, *, project_id: str, name: str) -> dict[str, Any] | None:
        cursor = self.conn.execute('SELECT id, project_id, name, kind, target, status, command_json, result_json, created_at, updated_at FROM evaluations WHERE project_id = ? AND name = ?', (project_id, name))
        row = cursor.fetchone()
        return _row_to_dict(cursor, row) if row is not None else None

    def propose_smoke_for_rule(self, *, rule_id: str, project_id: str = 'helpus-ai', evaluation_id: str | None = None, name: str | None = None) -> dict[str, Any]:
        rule = self.get_rule(rule_id)
        if rule['status'] not in {'draft', 'active'}:
            raise ValueError('only draft or active rules can receive evaluation proposals')
        eval_name = normalize_eval_name(name or ('smoke-' + rule['name']))
        existing = self.find_evaluation(project_id=project_id, name=eval_name)
        if existing is not None:
            return existing
        new_id = evaluation_id or ('eval-' + str(uuid.uuid4()))
        command = command_for_rule(rule['name'])
        result = {'source_rule_id': rule['id'], 'source_rule_name': rule['name'], 'proposal_only': True}
        self.conn.execute('INSERT INTO evaluations (id, project_id, name, kind, target, status, command_json, result_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (new_id, project_id, eval_name, 'smoke_proposal', rule['id'], 'proposed', _json_dumps(command), _json_dumps(result)))
        self.conn.commit()
        return self.get_evaluation(new_id)

    def list_evaluations(self, *, project_id: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if limit < 1 or limit > 500:
            raise ValueError('limit must be between 1 and 500')
        clauses: list[str] = []
        params: list[Any] = []
        if project_id is not None:
            clauses.append('project_id = ?')
            params.append(project_id)
        if status is not None:
            clauses.append('status = ?')
            params.append(status)
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        cursor = self.conn.execute(f'SELECT id, project_id, name, kind, target, status, command_json, result_json, created_at, updated_at FROM evaluations{where} ORDER BY created_at DESC, id DESC LIMIT ?', (*params, limit))
        return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
