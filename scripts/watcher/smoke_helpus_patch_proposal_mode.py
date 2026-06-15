from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_patch_proposal_mode import build_helpus_patch_proposal

def test_patch_proposal_defaults() -> None:
    proposal = build_helpus_patch_proposal("melhorar resposta operacional")
    assert proposal["mode"] == "proposal_only"
    assert proposal["can_apply_automatically"] is False
    assert proposal["requires_human_approval"] is True
    assert "git diff --check" in proposal["required_validations"]

def test_patch_proposal_allowlist() -> None:
    proposal = build_helpus_patch_proposal(
        "Micro 26 patch proposal",
        allowed_files=["backend/x.py"],
        proposed_steps=["show diff"],
    )
    assert proposal["allowed_files"] == ["backend/x.py"]
    assert proposal["proposed_steps"] == ["show diff"]
    assert proposal["risk_level"] == "medium"

if __name__ == "__main__":
    test_patch_proposal_defaults()
    test_patch_proposal_allowlist()
    print("OK smoke_helpus_patch_proposal_mode")
