from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.evolving_memory_operator_dashboard import (
    OperatorDashboardSummary,
    build_operator_dashboard_summary,
)


def test_operator_dashboard_summary() -> None:
    source = (ROOT / "backend" / "evolving_memory_operator_dashboard.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "memory.db"
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "create table evolving_memory_events (project_id text, event_type text, status text, severity text, created_at text)"
            )
            conn.execute(
                "create table evolving_memory_commands (project_id text, command_id text, status text, created_at text)"
            )
            conn.execute(
                "create table evolving_memory_lessons (project_id text, title text, status text, created_at text)"
            )
            conn.execute(
                "create table evolving_memory_rules (project_id text, title text, status text, created_at text)"
            )
            conn.execute(
                "create table evolving_memory_evaluation_proposals (project_id text, title text, status text, created_at text)"
            )
            conn.execute(
                "insert into evolving_memory_events values (?, ?, ?, ?, ?)",
                ("helpusai", "smoke", "ok", "info", "2026-06-15T00:00:00Z"),
            )
            conn.execute(
                "insert into evolving_memory_commands values (?, ?, ?, ?)",
                ("helpusai", "cmd-readonly", "ok", "2026-06-15T00:00:00Z"),
            )
            conn.execute(
                "insert into evolving_memory_lessons values (?, ?, ?, ?)",
                ("helpusai", "Keep changes gated", "draft", "2026-06-15T00:00:00Z"),
            )
            conn.execute(
                "insert into evolving_memory_rules values (?, ?, ?, ?)",
                ("helpusai", "No automatic activation", "draft", "2026-06-15T00:00:00Z"),
            )
            conn.execute(
                "insert into evolving_memory_evaluation_proposals values (?, ?, ?, ?)",
                ("helpusai", "Review dashboard output", "proposed", "2026-06-15T00:00:00Z"),
            )
            conn.commit()
        finally:
            conn.close()

        summary = OperatorDashboardSummary(db_path=db_path, project_id="helpusai").generate()
        summary_from_helper = build_operator_dashboard_summary(db_path=db_path, project_id="helpusai")

    assert summary["STATUS"] == "ok"
    assert summary["summary"]["readonly"] is True
    assert summary["summary"]["project_id"] == "helpusai"
    assert summary["counts"]["events"] == 1
    assert summary["counts"]["commands"] == 1
    assert summary["counts"]["lessons"] == 1
    assert summary["counts"]["rules"] == 1
    assert summary["counts"]["evaluations"] == 1
    assert summary["recent"]["events"]
    assert summary["recent"]["commands"]
    assert summary["recent"]["lessons"]
    assert summary["recent"]["rules"]
    assert summary["recent"]["evaluations"]
    assert summary["next_safe_actions"]
    assert any("readonly" in action.lower() for action in summary["next_safe_actions"])
    assert any("do not activate rules" in action.lower() for action in summary["next_safe_actions"])
    assert summary_from_helper["counts"] == summary["counts"]


def test_missing_database_is_safe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "missing.db"
        summary = OperatorDashboardSummary(db_path=db_path, project_id="helpusai").generate()

    assert summary["STATUS"] == "database_missing"
    assert summary["summary"]["readonly"] is True
    assert summary["counts"]["events"] == 0
    assert summary["next_safe_actions"]


if __name__ == "__main__":
    test_operator_dashboard_summary()
    test_missing_database_is_safe()
    print("OK smoke_evolving_memory_operator_dashboard")
