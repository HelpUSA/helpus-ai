from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from evolving_memory_evaluation_proposals import EvaluationProposalGenerator, command_for_rule, normalize_eval_name


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def insert_rule(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("INSERT INTO rules (id, scope, name, rule_text, priority, enabled, status) VALUES (?, ?, ?, ?, ?, ?, ?)", ("rule-1", "helpus-ai", "generated-code-syntax-error", "Run py_compile before commit", 60, 0, "draft"))
    conn.commit()
    conn.close()


def main() -> None:
    source = (ROOT / "backend" / "evolving_memory_evaluation_proposals.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "proposal generator must not execute commands")
    assert_true("import requests" not in source, "proposal generator must not import requests")
    assert_true(normalize_eval_name("Smoke: Generated Code!") == "smoke-generated-code", "eval name normalized")
    assert_true(command_for_rule("generated-code-syntax-error") == ["python", "scripts/watcher/smoke_rule_generated_code_syntax_error.py"], "command proposal generated")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "memory.sqlite"
        generator = EvaluationProposalGenerator(db_path)
        try:
            insert_rule(db_path)
            evaluation = generator.propose_smoke_for_rule(rule_id="rule-1", project_id="helpus-ai", evaluation_id="eval-1")
            assert_true(evaluation["id"] == "eval-1", "evaluation id persisted")
            assert_true(evaluation["project_id"] == "helpus-ai", "project persisted")
            assert_true(evaluation["name"] == "smoke-generated-code-syntax-error", "evaluation name from rule")
            assert_true(evaluation["kind"] == "smoke_proposal", "kind persisted")
            assert_true(evaluation["target"] == "rule-1", "target is rule id")
            assert_true(evaluation["status"] == "proposed", "status proposed")
            command = json.loads(evaluation["command_json"])
            assert_true(command[0] == "python", "command json persisted")
            result = json.loads(evaluation["result_json"])
            assert_true(result["proposal_only"] is True, "proposal only marker persisted")
            again = generator.propose_smoke_for_rule(rule_id="rule-1", project_id="helpus-ai", evaluation_id="eval-duplicate")
            assert_true(again["id"] == "eval-1", "duplicate proposal returns existing evaluation")
            evaluations = generator.list_evaluations(project_id="helpus-ai", status="proposed", limit=10)
            assert_true(len(evaluations) == 1, "list evaluations filters proposed")
            try:
                generator.list_evaluations(limit=0)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid limit accepted")
        finally:
            generator.close()

    print("EVOLVING_MEMORY_EVALUATION_PROPOSALS_SMOKE_OK")


if __name__ == "__main__":
    main()
