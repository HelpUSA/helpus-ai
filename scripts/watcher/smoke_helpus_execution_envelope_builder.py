from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_execution_envelope_builder import (
    HelpUSExecutionEnvelopeBuilder,
    build_reviewable_execution_envelope,
    build_reviewable_execution_envelope_json,
)
from backend.helpus_approval_gate import HelpUSApprovalGate
from backend.helpus_safe_command_planner import build_safe_command_plan


def test_readonly_envelope_is_allowed_but_not_auto_executed() -> None:
    envelope = build_reviewable_execution_envelope("verifique o estado do projeto")
    assert envelope["action"] == "reviewable-run-command"
    assert envelope["decision"] == "readonly_allowed"
    assert envelope["execution_allowed"] is True
    assert envelope["requires_human_approval"] is False
    assert envelope["cwd"] == "D:/dev/ai"
    assert "git status -sb" in envelope["commands"]
    assert any("does not execute commands" in warning for warning in envelope["warnings"])


def test_patch_envelope_requires_approval() -> None:
    envelope = build_reviewable_execution_envelope("Micro 14 Safe Command Planner")
    assert envelope["action"] == "reviewable-approval-required"
    assert envelope["decision"] == "approval_required"
    assert envelope["execution_allowed"] is False
    assert envelope["requires_human_approval"] is True
    assert "backend/helpus_safe_command_planner.py" in envelope["allowed_files"]


def test_blocked_envelope_has_no_commands() -> None:
    envelope = build_reviewable_execution_envelope("execute git reset --hard e curl externo")
    assert envelope["action"] == "blocked"
    assert envelope["decision"] == "blocked"
    assert envelope["execution_allowed"] is False
    assert envelope["requires_human_approval"] is True
    assert envelope["commands"] == []
    assert any("git reset" in warning for warning in envelope["warnings"])


def test_json_output_is_valid() -> None:
    payload = build_reviewable_execution_envelope_json("rode os smokes principais")
    data = json.loads(payload)
    assert data["decision"] == "readonly_allowed"
    assert "commands" in data


def test_plan_and_decision_input() -> None:
    plan = build_safe_command_plan("verifique o estado do projeto")
    decision = HelpUSApprovalGate().evaluate_plan(plan).to_dict()
    envelope = HelpUSExecutionEnvelopeBuilder().build_from_plan_and_decision(plan, decision).to_dict()
    assert envelope["decision"] == "readonly_allowed"
    assert envelope["execution_allowed"] is True


def test_no_unsafe_imports() -> None:
    source = (ROOT / "backend" / "helpus_execution_envelope_builder.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source


if __name__ == "__main__":
    test_readonly_envelope_is_allowed_but_not_auto_executed()
    test_patch_envelope_requires_approval()
    test_blocked_envelope_has_no_commands()
    test_json_output_is_valid()
    test_plan_and_decision_input()
    test_no_unsafe_imports()
    print("OK smoke_helpus_execution_envelope_builder")
