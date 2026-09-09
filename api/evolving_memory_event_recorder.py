from __future__ import annotations

from pathlib import Path
from typing import Any

from evolving_memory_store import EvolvingMemoryStore

from evolving_memory_sanitizer import sanitize_metadata, sanitize_text


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
		'metadata': sanitize_metadata(metadata),
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
