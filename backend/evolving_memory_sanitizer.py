from __future__ import annotations

from typing import Any

MAX_TEXT_LENGTH = 4000
SECRET_MARKERS = ('api_key=', 'apikey=', 'token=', 'secret=', 'password=', 'authorization:', 'bearer ', 'sk-')

def sanitize_text(value: str | None, *, max_length: int = MAX_TEXT_LENGTH) -> str | None:
	if value is None:
		return None
	cleaned = str(value).replace(chr(0), '')
	lowered = cleaned.lower()
	for marker in SECRET_MARKERS:
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

def sanitize_metadata(value: dict[str, Any] | None) -> dict[str, Any]:
	out: dict[str, Any] = {}
	for key, item in (value or {}).items():
		low_key = str(key).lower()
		if any(marker.strip('=: ').strip() in low_key for marker in SECRET_MARKERS):
			out[str(key)] = '<redacted>'
		elif isinstance(item, str):
			out[str(key)] = sanitize_text(item)
		else:
			out[str(key)] = item
	return out

def sanitize_command_result_fields(*, stdout: str = '', stderr: str = '', diff_stat: str = '', summary: str | None = None) -> dict[str, str | None]:
	return {
		'stdout': sanitize_text(stdout) or '',
		'stderr': sanitize_text(stderr) or '',
		'diff_stat': sanitize_text(diff_stat) or '',
		'summary': sanitize_text(summary),
	}
