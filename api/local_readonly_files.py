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
    forbidden_names = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "credentials.json",
        "id_rsa",
        "id_dsa",
    }
    forbidden_markers = ("secret", "token", "password", "passwd", "private_key", "apikey", "api_key")
    text_suffixes = (".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".txt", ".yml", ".yaml", ".toml", ".css", ".html", ".csv")

    def __init__(self, root: Path | str, max_bytes: int = 20000, max_files: int = 300) -> None:
        self.root = Path(root).resolve()
        self.max_bytes = max_bytes
        self.max_files = max_files

    def _reject_if_secret_path(self, resolved: Path, normalized: str) -> None:
        lower_name = resolved.name.lower()
        lower_path = normalized.lower()
        if lower_name in self.forbidden_names:
            raise ValueError("secret_path_blocked")
        if any(marker in lower_path for marker in self.forbidden_markers):
            raise ValueError("secret_marker_blocked")

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
        self._reject_if_secret_path(resolved, normalized)
        return resolved

    def _normalize_dir(self, relative_path: str = "docs/") -> Path:
        raw = str(relative_path or "docs/").replace(chr(92), "/").strip()
        if not raw:
            raw = "docs/"
        candidate = Path(raw)
        if candidate.is_absolute():
            raise ValueError("absolute_path_blocked")
        resolved = (self.root / candidate).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError("path_traversal_blocked") from exc
        normalized = resolved.relative_to(self.root).as_posix()
        normalized_dir = normalized if normalized.endswith("/") else f"{normalized}/"
        if not any(normalized_dir.startswith(prefix) for prefix in self.allowed_prefixes):
            raise ValueError("path_not_allowed")
        self._reject_if_secret_path(resolved, normalized)
        return resolved

    def _is_safe_result_path(self, path: Path) -> bool:
        try:
            normalized = path.resolve().relative_to(self.root).as_posix()
            if not normalized.startswith(self.allowed_prefixes):
                return False
            self._reject_if_secret_path(path, normalized)
            return True
        except (OSError, ValueError):
            return False

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

    def list_files(self, relative_path: str = "docs/", limit: int = 200) -> dict:
        try:
            resolved = self._normalize_dir(relative_path)
            if not resolved.exists():
                return {"ok": False, "path": relative_path, "files": [], "truncated": False, "reason": "not_found"}
            if not resolved.is_dir():
                return {"ok": False, "path": relative_path, "files": [], "truncated": False, "reason": "not_dir"}
            safe_limit = max(1, min(int(limit), self.max_files))
            files = []
            for child in sorted(resolved.rglob("*")):
                if not child.is_file() or not self._is_safe_result_path(child):
                    continue
                normalized = child.resolve().relative_to(self.root).as_posix()
                files.append({"path": normalized, "size": child.stat().st_size})
                if len(files) >= safe_limit:
                    break
            return {"ok": True, "path": resolved.relative_to(self.root).as_posix(), "files": files, "truncated": len(files) >= safe_limit, "reason": "ok"}
        except ValueError as exc:
            return {"ok": False, "path": relative_path, "files": [], "truncated": False, "reason": str(exc)}

    def search_text(self, query: str, relative_path: str = "docs/", limit: int = 50) -> dict:
        q = str(query or "").strip()
        if len(q) < 2:
            return {"ok": False, "query": q, "path": relative_path, "matches": [], "truncated": False, "reason": "query_too_short"}
        try:
            resolved = self._normalize_dir(relative_path)
            if not resolved.exists():
                return {"ok": False, "query": q, "path": relative_path, "matches": [], "truncated": False, "reason": "not_found"}
            if not resolved.is_dir():
                return {"ok": False, "query": q, "path": relative_path, "matches": [], "truncated": False, "reason": "not_dir"}
            safe_limit = max(1, min(int(limit), 100))
            needle = q.lower()
            matches = []
            scanned = 0
            for child in sorted(resolved.rglob("*")):
                if not child.is_file() or child.suffix.lower() not in self.text_suffixes:
                    continue
                if not self._is_safe_result_path(child):
                    continue
                if child.stat().st_size > max(self.max_bytes * 5, 100000):
                    continue
                scanned += 1
                text = child.read_text(encoding="utf-8", errors="replace")
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if needle in line.lower():
                        matches.append({"path": child.resolve().relative_to(self.root).as_posix(), "line": line_number, "text": line.strip()[:240]})
                        if len(matches) >= safe_limit:
                            return {"ok": True, "query": q, "path": resolved.relative_to(self.root).as_posix(), "matches": matches, "scanned_files": scanned, "truncated": True, "reason": "ok"}
            return {"ok": True, "query": q, "path": resolved.relative_to(self.root).as_posix(), "matches": matches, "scanned_files": scanned, "truncated": False, "reason": "ok"}
        except ValueError as exc:
            return {"ok": False, "query": q, "path": relative_path, "matches": [], "truncated": False, "reason": str(exc)}
