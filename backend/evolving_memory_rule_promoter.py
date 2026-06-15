from __future__ import annotations

import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from evolving_memory_schema import apply_schema, connect_memory_db

def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
	names = [description[0] for description in cursor.description]
	return dict(zip(names, row))

def normalize_rule_name(value: str) -> str:
	slug = re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')
	return slug or f'rule-{uuid.uuid4().hex[:8]}'

def priority_from_severity(severity: str | None) -> int:
	severity = (severity or 'low').lower()
	if severity == 'high':
		return 80
	if severity == 'medium':
		return 60
	return 40

class RuleDraftPromoter:
	def __init__(self, db_path: str | Path = ':memory:') -> None:
		self.db_path = str(db_path)
		self.conn = connect_memory_db(self.db_path)
		apply_schema(self.conn)

	def close(self) -> None:
		self.conn.close()

	def get_lesson(self, lesson_id: str) -> dict[str, Any]:
		cursor = self.conn.execute('SELECT id, project_id, problem, root_cause, lesson, rule_text, severity, status, created_at FROM lessons WHERE id = ?', (lesson_id,))
		row = cursor.fetchone()
		if row is None:
			raise KeyError(lesson_id)
		return _row_to_dict(cursor, row)

	def get_rule(self, rule_id: str) -> dict[str, Any]:
		cursor = self.conn.execute('SELECT id, scope, name, rule_text, priority, enabled, status, created_at, updated_at FROM rules WHERE id = ?', (rule_id,))
		row = cursor.fetchone()
		if row is None:
			raise KeyError(rule_id)
		return _row_to_dict(cursor, row)

	def find_rule(self, *, scope: str, name: str) -> dict[str, Any] | None:
		cursor = self.conn.execute('SELECT id, scope, name, rule_text, priority, enabled, status, created_at, updated_at FROM rules WHERE scope = ? AND name = ?', (scope, name))
		row = cursor.fetchone()
		return _row_to_dict(cursor, row) if row is not None else None

	def promote_lesson_to_rule_draft(self, *, lesson_id: str, scope: str = 'helpus-ai', name: str | None = None, rule_id: str | None = None) -> dict[str, Any]:
		lesson = self.get_lesson(lesson_id)
		if lesson['status'] != 'draft':
			raise ValueError('only draft lessons can be promoted to rule drafts')
		rule_name = normalize_rule_name(name or lesson['root_cause'])
		existing = self.find_rule(scope=scope, name=rule_name)
		if existing is not None:
			return existing
		new_id = rule_id or f'rule-{uuid.uuid4()}'
		self.conn.execute('INSERT INTO rules (id, scope, name, rule_text, priority, enabled, status) VALUES (?, ?, ?, ?, ?, 0, ?)', (new_id, scope, rule_name, lesson['rule_text'], priority_from_severity(lesson['severity']), 'draft'))
		self.conn.commit()
		return self.get_rule(new_id)

	def list_rules(self, *, scope: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
		if limit < 1 or limit > 500:
			raise ValueError('limit must be between 1 and 500')
		clauses: list[str] = []
		params: list[Any] = []
		if scope is not None:
			clauses.append('scope = ?')
			params.append(scope)
		if status is not None:
			clauses.append('status = ?')
			params.append(status)
		where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
		cursor = self.conn.execute(f'SELECT id, scope, name, rule_text, priority, enabled, status, created_at, updated_at FROM rules{where} ORDER BY priority DESC, created_at DESC, id DESC LIMIT ?', (*params, limit))
		return [_row_to_dict(cursor, row) for row in cursor.fetchall()]
