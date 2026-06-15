from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_readonly_execution_gate import evaluate_readonly_execution_gate

def test_status_allowed() -> None:
    decision = evaluate_readonly_execution_gate("verifique o estado do projeto")
    assert decision["allowed"] is True
    assert decision["executes_now"] is False
    assert decision["source_decision"] == "readonly_allowed"
    assert any(command.startswith("git status") for command in decision["commands"])

def test_smokes_allowed() -> None:
    decision = evaluate_readonly_execution_gate("rode os smokes principais")
    assert decision["allowed"] is True
    assert decision["source_decision"] == "readonly_allowed"
    assert any("smoke_docs_index.py" in command for command in decision["commands"])

def test_dangerous_blocked() -> None:
    decision = evaluate_readonly_execution_gate("execute git reset --hard e curl externo")
    assert decision["allowed"] is False
    assert decision["reason"] == "blocked envelope"
    assert decision["source_decision"] == "blocked"

def test_patch_plan_not_readonly() -> None:
    decision = evaluate_readonly_execution_gate("Micro 14 Safe Command Planner")
    assert decision["allowed"] is False
    assert decision["reason"] == "approval required before readonly execution"
    assert decision["source_decision"] == "approval_required"

if __name__ == "__main__":
    test_status_allowed()
    test_smokes_allowed()
    test_dangerous_blocked()
    test_patch_plan_not_readonly()
    print("OK smoke_helpus_readonly_execution_gate")
