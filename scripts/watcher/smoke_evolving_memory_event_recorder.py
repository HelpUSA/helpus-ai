from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))

from evolving_memory_event_recorder import WatcherEventRecorder, sanitize_text

def assert_true(condition, message):
	if not condition:
		raise AssertionError(message)

def main() -> None:
	source = (ROOT / 'backend' / 'evolving_memory_event_recorder.py').read_text(encoding='utf-8')
	assert_true('subprocess' not in source, 'recorder must not execute commands')
	assert_true('requests' not in source, 'recorder must not call network')
	redacted = sanitize_text('OPENAI_API_KEY=sk-abc123456789xyz token=supersecret')
	assert_true('<redacted>' in redacted, 'secrets are redacted')
	assert_true('supersecret' not in redacted, 'token value is hidden')
	assert_true(sanitize_text('x' * 4100).endswith('...<truncated>'), 'long text is truncated')
	with tempfile.TemporaryDirectory() as tmp:
		recorder = WatcherEventRecorder(Path(tmp) / 'memory.sqlite')
		event = recorder.record_watcher_event({'event_id': 'watcher-event-1', 'project_id': 'helpus-ai', 'event_type': 'watcher_error_received', 'command_id': 'cmd-1', 'status': 'failed', 'return_code': 1, 'stdout': 'ok', 'stderr': 'Authorization: bearer abcdefghijklmnop', 'metadata': {'micro': 3}})
		assert_true(event['id'] == 'watcher-event-1', 'event id persisted')
		assert_true(event['event_type'] == 'watcher_error_received', 'event type persisted')
		assert_true('abcdefghijklmnop' not in (event['output_text'] or ''), 'stderr sanitized')
		metadata = json.loads(event['metadata_json'])
		assert_true(metadata['command_id'] == 'cmd-1', 'command id metadata persisted')
		assert_true(metadata['micro'] == 3, 'metadata retained')
		recorder.record_watcher_event({'project_id': 'helpus-ai', 'type': 'command_succeeded', 'stdout': 'done'})
		events = recorder.list_project_events('helpus-ai', limit=10)
		assert_true(len(events) == 2, 'two events listed')
		recorder.close()
	print('EVOLVING_MEMORY_EVENT_RECORDER_SMOKE_OK')

if __name__ == '__main__':
	main()
