from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from evolving_memory_report import EvolvingMemoryReport


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def seed(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("INSERT INTO rules (id, scope, name, rule_text, priority, enabled, status) VALUES (?, ?, ?, ?, ?, ?, ?)", ("rule-1", "helpus-ai", "generated-code-syntax-error", "Run py_compile before commit", 60, 0, "draft"))
    conn.execute("INSERT INTO lessons (id, project_id, trigger_event_id, problem, root_cause, lesson, rule_text, severity, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", ("lesson-1", "helpus-ai", None, "generated code failed", "generated_code_syntax_error", "Validate generated code", "Run py_compile", "medium", "draft"))
    conn.execute("INSERT INTO evaluations (id, project_id, name, kind, target, status, command_json, result_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("eval-1", "helpus-ai", "smoke-generated-code", "smoke_proposal", "rule-1", "proposed", "[]", "{}"))
    conn.execute("INSERT INTO command_requests (id, command_id, project_id, cwd, command_json, reason, risk_level, requires_confirmation) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ("req-1", "cmd-1", "helpus-ai", "D:/dev/ai", "[]", "smoke", "low", 0))
    conn.execute("INSERT INTO command_results (id, command_request_id, return_code, stdout, stderr, summary) VALUES (?, ?, ?, ?, ?, ?)", ("res-1", "req-1", 1, "", "error", "failed"))
    conn.commit()
    conn.close()


def main() -> None:
    source = (ROOT / "backend" / "evolving_memory_report.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "report must not execute commands")
    assert_true("import requests" not in source, "report must not import requests")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "memory.sqlite"
        report = EvolvingMemoryReport(db_path)
        try:
            seed(db_path)
            data = report.snapshot(project_id="helpus-ai", limit=10)
            assert_true(data["counts"]["rules"] == 1, "rule count")
            assert_true(data["counts"]["lessons"] == 1, "lesson count")
            assert_true(data["counts"]["evaluations"] == 1, "evaluation count")
            assert_true(data["counts"]["command_requests"] == 1, "command request count")
            assert_true(data["counts"]["command_results"] == 1, "command result count")
            assert_true(len(data["failed_command_results"]) == 1, "failure listed")
            markdown = report.render_markdown(project_id="helpus-ai", limit=10)
            assert_true("# Evolving Memory Report: helpus-ai" in markdown, "markdown title")
            assert_true("generated-code-syntax-error" in markdown, "rule appears in markdown")
            exported = json.loads(report.export_json(project_id="helpus-ai", limit=10))
            assert_true(exported["project_id"] == "helpus-ai", "json project")
            try:
                report.snapshot(limit=0)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid limit accepted")
        finally:
            report.close()

    print("EVOLVING_MEMORY_REPORT_SMOKE_OK")


if __name__ == "__main__":
    main()
