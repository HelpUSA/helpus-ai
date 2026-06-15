from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_approval_gate import (
    HelpUSApprovalGate,
    evaluate_helpus_command_intent,
    evaluate_helpus_command_plan,
)
from backend.helpus_safe_command_planner import build_safe_command_plan


def test_readonly_status_is_allowed() -> None:
    decision = evaluate_helpus_command_intent("verifique o estado do projeto")
    assert decision["decision"] == "readonly_allowed"
    assert decision["can_execute_readonly"] is True
    assert decision["requires_human_approval"] is False
    assert decision["is_blocked"] is False
    assert "git status -sb" in decision["allowed_commands"]


def test_smokes_are_readonly_allowed() -> None:
    decision = evaluate_helpus_command_intent("rode os smokes principais")
    assert decision["decision"] == "readonly_allowed"
    assert decision["can_execute_readonly"] is True
    assert "python scripts/watcher/smoke_docs_index.py" in decision["allowed_commands"]


def test_patch_plan_requires_approval() -> None:
    plan = build_safe_command_plan("Micro 14 Safe Command Planner")
    decision = HelpUSApprovalGate().evaluate_plan(plan).to_dict()
    assert decision["decision"] == "approval_required"
    assert decision["can_execute_readonly"] is False
    assert decision["requires_human_approval"] is True
    assert decision["is_blocked"] is False
    assert "backend/helpus_safe_command_planner.py" in decision["allowed_files"]


def test_dangerous_intent_is_blocked() -> None:
    decision = evaluate_helpus_command_intent("execute git reset --hard e curl externo")
    assert decision["decision"] == "blocked"
    assert decision["is_blocked"] is True
    assert decision["can_execute_readonly"] is False
    assert decision["requires_human_approval"] is True
    assert decision["allowed_commands"] == []
    assert any("git reset" in reason for reason in decision["reasons"])


def test_dict_plan_evaluation() -> None:
    plan = {
        "intent": "manual plan",
        "risk_level": "medium",
        "commands": ["python smoke.py"],
        "allowed_files": ["x.py"],
        "blocked_reasons": [],
        "requires_human_approval": True,
        "stop_on_failure": True,
    }
    decision = evaluate_helpus_command_plan(plan)
    assert decision["decision"] == "approval_required"
    assert decision["allowed_files"] == ["x.py"]


def test_no_unsafe_imports() -> None:
    source = (ROOT / "backend" / "helpus_approval_gate.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source


if __name__ == "__main__":
    test_readonly_status_is_allowed()
    test_smokes_are_readonly_allowed()
    test_patch_plan_requires_approval()
    test_dangerous_intent_is_blocked()
    test_dict_plan_evaluation()
    test_no_unsafe_imports()
    print("OK smoke_helpus_approval_gate")
