from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass(frozen=True)
class ReadonlyFileResult:
    ok: bool
    path: str
    size: int
    content: str
    truncated: bool
    reason: str

class LocalReadonlyFiles:
    allowed_prefixes = ("docs/", "reports/", "scripts/watcher/", "backend/")
    forbidden_names = {".env", ".env.local", ".env.production", ".env.development", "credentials.json", "id_rsa", "id_dsa"}
    forbidden_markers = ("secret", "token", "password", "passwd", "private_key", "apikey", "api_key")

    def __init__(self, root: Path | str, max_bytes: int = 20000) -> None:
        self.root = Path(root).resolve()
        self.max_bytes = max_bytes

    def _normalize(self, relative_path: str) -> Path:
        if not relative_path or not str(relative_path).strip():
            raise ValueError("path_required")
        raw = str(relative_path).replace(chr(92), "/").strip()
        candidate = Path(raw)
        if candidate.is_absolute():
            raise ValueError("absolute_path_blocked")
        resolved = (self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("path_traversal_blocked") from exc
        normalized = resolved.relative_to(self.root).as_posix()
        if not normalized.startswith(self.allowed_prefixes):
            raise ValueError("path_not_allowed")
        lower_name = resolved.name.lower()
        lower_path = normalized.lower()
        if lower_name in self.forbidden_names:
            raise ValueError("secret_path_blocked")
        if any(marker in lower_path for marker in self.forbidden_markers):
            raise ValueError("secret_marker_blocked")
        return resolved

    def read_text(self, relative_path: str) -> dict:
        try:
            resolved = self._normalize(relative_path)
            if not resolved.exists():
                return asdict(ReadonlyFileResult(False, relative_path, 0, "", False, "not_found"))
            if not resolved.is_file():
                return asdict(ReadonlyFileResult(False, relative_path, 0, "", False, "not_file"))
            size = resolved.stat().st_size
            normalized = resolved.relative_to(self.root).as_posix()
            if size > self.max_bytes:
                data = resolved.read_bytes()[: self.max_bytes]
                return asdict(ReadonlyFileResult(True, normalized, size, data.decode("utf-8", errors="replace"), True, "truncated"))
            content = resolved.read_text(encoding="utf-8", errors="replace")
            return asdict(ReadonlyFileResult(True, normalized, size, content, False, "ok"))
        except ValueError as exc:
            return asdict(ReadonlyFileResult(False, relative_path, 0, "", False, str(exc)))
