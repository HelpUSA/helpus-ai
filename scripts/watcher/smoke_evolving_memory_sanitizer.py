from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))

from evolving_memory_sanitizer import sanitize_command_result_fields, sanitize_metadata, sanitize_text

def assert_true(condition, message):
	if not condition:
		raise AssertionError(message)

def main() -> None:
	source = (ROOT / 'backend' / 'evolving_memory_sanitizer.py').read_text(encoding='utf-8')
	assert_true('subprocess' not in source, 'sanitizer must not execute commands')
	assert_true('import requests' not in source, 'sanitizer must not import requests')
	redacted = sanitize_text('OPENAI_API_KEY=sk-abc123456789xyz token=supersecret Authorization: bearer abcdefghijklmnop')
	assert_true('<redacted>' in redacted, 'secrets are redacted')
	assert_true('supersecret' not in redacted, 'token value hidden')
	assert_true('abcdefghijklmnop' not in redacted, 'bearer value hidden')
	assert_true(sanitize_text('x' * 4100).endswith('...<truncated>'), 'long text truncated')
	metadata = sanitize_metadata({'token': 'abc123', 'safe': 'ok', 'nested_count': 2})
	assert_true(metadata['token'] == '<redacted>', 'metadata secret redacted')
	assert_true(metadata['safe'] == 'ok', 'safe metadata retained')
	fields = sanitize_command_result_fields(stdout='ok token=secret', stderr='Authorization: bearer abcdefghijklmnop', diff_stat='a.py | 1 +', summary='done')
	assert_true('secret' not in fields['stdout'], 'stdout sanitized')
	assert_true('abcdefghijklmnop' not in fields['stderr'], 'stderr sanitized')
	assert_true(fields['summary'] == 'done', 'summary retained')
	print('EVOLVING_MEMORY_SANITIZER_SMOKE_OK')

if __name__ == '__main__':
	main()
