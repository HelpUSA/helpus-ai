from __future__ import annotations

from pathlib import Path
from typing import Any

from evolving_memory_store import EvolvingMemoryStore

MAX_TEXT_LENGTH = 4000

def sanitize_text(value: str | None, *, max_length: int = MAX_TEXT_LENGTH) -> str | None:
	if value is None:
		return None
	cleaned = value.replace(chr(0), '')
	markers = ('api_key=', 'apikey=', 'token=', 'secret=', 'password=', 'authorization:', 'bearer ', 'sk-')
	lowered = cleaned.lower()
	for marker in markers:
		pos = lowered.find(marker)
		while pos >= 0:
			end = pos + len(marker)
			while end < len(cleaned) and cleaned[end] not in (' ', ',', ';', chr(10), chr(13), chr(9)):
				end += 1
			cleaned = cleaned[:pos] + marker + '<redacted>' + cleaned[end:]
			lowered = cleaned.lower()
			pos = lowered.find(marker, pos + len(marker) + 10)
	if len(cleaned) > max_length:
		return cleaned[:max_length] + '...<truncated>'
	return cleaned

def normalize_watcher_event(raw: dict[str, Any]) -> dict[str, Any]:
	event_type = str(raw.get('event_type') or raw.get('type') or 'watcher_event')
	project_id = str(raw.get('project_id') or 'helpus-ai')
	metadata = dict(raw.get('metadata') or {})
	for key in ('command_id', 'status', 'return_code', 'cwd', 'source'):
		if key in raw and key not in metadata:
			metadata[key] = raw[key]
	return {
		'project_id': project_id,
		'event_type': event_type,
		'agent_id': raw.get('agent_id'),
		'input_text': sanitize_text(raw.get('input_text') or raw.get('stdout')),
		'output_text': sanitize_text(raw.get('output_text') or raw.get('stderr')),
		'metadata': metadata,
		'event_id': raw.get('event_id'),
	}

class WatcherEventRecorder:
	def __init__(self, db_path: str | Path = ':memory:') -> None:
		self.store = EvolvingMemoryStore(db_path)

	def close(self) -> None:
		self.store.close()

	def record_watcher_event(self, raw: dict[str, Any]) -> dict[str, Any]:
		normalized = normalize_watcher_event(raw)
		return self.store.record_experience_event(**normalized)

	def list_project_events(self, project_id: str = 'helpus-ai', limit: int = 50) -> list[dict[str, Any]]:
		return self.store.list_experience_events(project_id=project_id, limit=limit)
