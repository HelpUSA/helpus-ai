from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

from evolving_memory_schema import apply_schema, connect_memory_db
from evolving_memory_sanitizer import sanitize_text

def _row_to_dict(cursor: sqlite3.Cursor, row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
	names = [description[0] for description in cursor.description]
	return dict(zip(names, row))

def classify_failure(*, return_code: int, stderr: str = '', summary: str | None = None) -> dict[str, str]:
	text = f'{stderr} {summary or ''}'.lower()
	if 'json' in text or 'parse' in text or 'escaped' in text:
		return {'root_cause': 'invalid_or_fragile_command_envelope', 'lesson': 'Prefer small commands or script_text/script_ext for complex watcher operations.', 'rule_text': 'For large watcher commands, avoid giant inline JSON/base64 and use smaller recoverable steps.', 'severity': 'medium'}
	if 'indentationerror' in text or 'syntaxerror' in text:
		return {'root_cause': 'generated_code_syntax_error', 'lesson': 'Validate generated code with py_compile before adding docs, commit or push.', 'rule_text': 'Every code patch must run py_compile and a focused smoke before commit.', 'severity': 'medium'}
	if return_code != 0:
		return {'root_cause': 'command_failed_without_specific_classifier', 'lesson': 'Failed command results should become draft lessons before repeating the same pattern.', 'rule_text': 'After a command failure, inspect stderr and create a draft lesson before retrying.', 'severity': 'low'}
	return {'root_cause': 'no_failure_detected', 'lesson': 'No lesson draft is needed for successful command results.', 'rule_text': 'Do not create failure lessons for successful command results.', 'severity': 'low'}

class LessonDraftExtractor:
	def __init__(self, db_path: str | Path = ':memory:') -> None:
		self.db_path = str(db_path)
		self.conn = connect_memory_db(self.db_path)
		apply_schema(self.conn)

	def close(self) -> None:
		self.conn.close()

	def create_lesson_from_command_result(self, *, project_id: str, command_result_id: str, return_code: int, stderr: str = '', summary: str | None = None, lesson_id: str | None = None) -> dict[str, Any] | None:
		if return_code == 0:
			return None
		if not project_id.strip():
			raise ValueError('project_id is required')
		if not command_result_id.strip():
			raise ValueError('command_result_id is required')
		classified = classify_failure(return_code=return_code, stderr=stderr, summary=summary)
		new_id = lesson_id or f'lesson-{uuid.uuid4()}'
		problem = sanitize_text(summary or stderr or f'command_result {command_result_id} failed') or 'command failed'
		self.conn.execute('INSERT INTO lessons (id, project_id, trigger_event_id, problem, root_cause, lesson, rule_text, severity, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (new_id, project_id, None, problem, classified['root_cause'], classified['lesson'], classified['rule_text'], classified['severity'], 'draft'))
		self.conn.commit()
		return self.get_lesson(new_id)

	def get_lesson(self, lesson_id: str) -> dict[str, Any]:
		cursor = self.conn.execute('SELECT id, project_id, trigger_event_id, problem, root_cause, lesson, rule_text, severity, status, created_at FROM lessons WHERE id = ?', (lesson_id,))
		row = cursor.fetchone()
		if row is None:
			raise KeyError(lesson_id)
		return _row_to_dict(cursor, row)

	def list_lessons(self, *, project_id: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
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
		cursor = self.conn.execute(f'SELECT id, project_id, trigger_event_id, problem, root_cause, lesson, rule_text, severity, status, created_at FROM lessons{where} ORDER BY created_at DESC, id DESC LIMIT ?', (*params, limit))
		return [_row_to_dict(cursor, row) for row in cursor.fetchall()]



