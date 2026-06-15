from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_human_approved_patch_apply import evaluate_human_approved_patch_apply

def test_missing_approval_blocks() -> None:
    decision = evaluate_human_approved_patch_apply(
        explicit_approval=False,
        requested_files=["backend/a.py"],
        allowed_files=["backend/a.py"],
    )
    assert decision["can_apply"] is False
    assert decision["reason"] == "explicit human approval missing"
    assert decision["applies_now"] is False

def test_outside_allowlist_blocks() -> None:
    decision = evaluate_human_approved_patch_apply(
        explicit_approval=True,
        requested_files=["backend/a.py", "backend/b.py"],
        allowed_files=["backend/a.py"],
    )
    assert decision["can_apply"] is False
    assert decision["blocked_files"] == ["backend/b.py"]

def test_approved_inside_allowlist_can_apply_decision_only() -> None:
    decision = evaluate_human_approved_patch_apply(
        explicit_approval=True,
        requested_files=["backend/a.py"],
        allowed_files=["backend/a.py"],
    )
    assert decision["can_apply"] is True
    assert decision["applies_now"] is False

if __name__ == "__main__":
    test_missing_approval_blocks()
    test_outside_allowlist_blocks()
    test_approved_inside_allowlist_can_apply_decision_only()
    print("OK smoke_helpus_human_approved_patch_apply")
