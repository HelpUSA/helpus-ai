from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class RepoCommandView:
    ok: bool
    return_code: int
    stdout: str
    stderr: str


class LocalRepoStatus:
    """Read-only git status and diff helper for the local repo."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()

    def _run(self, command: list[str]) -> dict:
        result = subprocess.run(
            command,
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return asdict(
            RepoCommandView(
                result.returncode == 0,
                result.returncode,
                result.stdout,
                result.stderr,
            )
        )

    def status(self) -> dict:
        branch = self._run(["git", "branch", "--show-current"])
        head = self._run(["git", "rev-parse", "--short", "HEAD"])
        porcelain = self._run(["git", "status", "--porcelain"])
        status_sb = self._run(["git", "status", "-sb"])
        dirty_files = [
            line[3:].strip().replace(chr(92), "/")
            for line in porcelain["stdout"].splitlines()
            if line.strip()
        ]
        return {
            "ok": branch["ok"] and head["ok"] and porcelain["ok"] and status_sb["ok"],
            "branch": branch["stdout"].strip(),
            "head": head["stdout"].strip(),
            "dirty_files": dirty_files,
            "status": status_sb["stdout"],
            "errors": [
                item["stderr"]
                for item in (branch, head, porcelain, status_sb)
                if item["stderr"]
            ],
        }

    def diff(self) -> dict:
        diff_stat = self._run(["git", "diff", "--stat"])
        diff_check = self._run(["git", "diff", "--check"])
        return {
            "ok": diff_stat["ok"] and diff_check["ok"],
            "stat": diff_stat["stdout"],
            "check_stdout": diff_check["stdout"],
            "check_stderr": diff_check["stderr"],
            "check_return_code": diff_check["return_code"],
        }