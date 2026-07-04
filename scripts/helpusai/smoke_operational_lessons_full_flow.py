from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def _run_smoke(rel: str) -> None:
    path = ROOT / rel
    if not path.exists():
        raise AssertionError(f"missing required smoke: {rel}")

    env = os.environ.copy()
    env.setdefault("HELPUS_OPERATIONAL_LESSONS_ENABLED", "1")
    env.setdefault("HELPUS_MEMORY_CONTEXT_ENABLED", "1")

    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        raise AssertionError(f"smoke failed: {rel}")


def _read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        raise AssertionError(f"missing required file: {rel}")
    return path.read_text(encoding="utf-8", errors="replace")


def _assert_contains(rel: str, markers: list[str]) -> None:
    text = _read(rel)
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise AssertionError(f"{rel} missing markers: {missing}")


def main() -> int:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(BACKEND))

    _run_smoke("scripts/helpusai/smoke_operational_lessons.py")
    _run_smoke("scripts/helpusai/smoke_operational_lesson_context.py")
    _run_smoke("scripts/helpusai/smoke_admin_operational_lessons_panel.py")

    obsidian_smoke = ROOT / "scripts/helpusai/smoke_obsidian_operational_lessons.py"
    if obsidian_smoke.exists():
        _run_smoke("scripts/helpusai/smoke_obsidian_operational_lessons.py")

    _assert_contains(
        "backend/main.py",
        [
            "/admin/operational-lessons",
            "build_admin_operational_lessons_panel",
            "append_operational_lesson_context",
        ],
    )
    _assert_contains(
        "backend/helpus_operational_lessons.py",
        [
            "OperationalLesson",
            "build_admin_operational_lessons_panel",
            "operational_lessons_enabled",
        ],
    )
    _assert_contains(
        "backend/helpus_operational_lesson_context.py",
        [
            "helpus_operational_lessons",
            "append_operational_lesson_context",
        ],
    )
    _assert_contains(
        "scripts/helpusai/export_obsidian_operational_lessons.py",
        [
            "operational",
            "lesson",
            "obsidian",
        ],
    )

    print("OK smoke_operational_lessons_full_flow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
