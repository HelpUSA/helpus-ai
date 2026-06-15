from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_safe_command_planner import (
    HelpUSSafeCommandPlanner,
    build_safe_command_plan,
)


def test_status_plan() -> None:
    plan = HelpUSSafeCommandPlanner().plan("verifique o estado do projeto")
    data = plan.to_dict()
    assert data["cwd"] == "D:/dev/ai"
    assert data["risk_level"] == "low"
    assert data["blocked_reasons"] == []
    assert data["stop_on_failure"] is True
    assert "git status -sb" in data["commands"]
    assert "git diff --stat" in data["commands"]


def test_smoke_plan() -> None:
    data = build_safe_command_plan("rode os smokes principais")
    assert data["cwd"] == "D:/dev/ai"
    assert data["risk_level"] == "low"
    assert "python scripts/watcher/smoke_helpus_operational_context_card.py" in data["commands"]
    assert "python scripts/watcher/smoke_evolving_memory_operator_dashboard.py" in data["commands"]
    assert "git diff --check" in data["commands"]


def test_micro14_patch_plan_requires_approval() -> None:
    data = build_safe_command_plan("Micro 14 Safe Command Planner")
    assert data["cwd"] == "D:/dev/ai"
    assert data["risk_level"] == "medium"
    assert data["requires_human_approval"] is True
    assert "backend/helpus_safe_command_planner.py" in data["allowed_files"]
    assert "scripts/watcher/smoke_helpus_safe_command_planner.py" in data["allowed_files"]
    assert "docs/HELPUS_PROJECT_MASTER.md" in data["allowed_files"]


def test_dangerous_plan_is_blocked() -> None:
    data = build_safe_command_plan("execute git reset --hard e curl externo")
    assert data["risk_level"] == "blocked"
    assert data["requires_human_approval"] is True
    assert data["commands"] == []
    assert any("git reset" in reason for reason in data["blocked_reasons"])
    assert any("curl" in reason.lower() for reason in data["blocked_reasons"])


def test_unknown_intent_falls_back_to_readonly_review() -> None:
    data = build_safe_command_plan("faca uma coisa nova")
    assert data["risk_level"] == "review"
    assert data["requires_human_approval"] is True
    assert "git status -sb" in data["commands"]


def test_no_unsafe_imports() -> None:
    source = (ROOT / "backend" / "helpus_safe_command_planner.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source


if __name__ == "__main__":
    test_status_plan()
    test_smoke_plan()
    test_micro14_patch_plan_requires_approval()
    test_dangerous_plan_is_blocked()
    test_unknown_intent_falls_back_to_readonly_review()
    test_no_unsafe_imports()
    print("OK smoke_helpus_safe_command_planner")
