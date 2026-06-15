from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_final_release_readiness import (
    HELPUSAI_FINAL_VERSION,
    REQUIRED_FINAL_SMOKES,
    build_helpus_final_release_readiness,
)

def test_final_release_readiness() -> None:
    readiness = build_helpus_final_release_readiness()
    assert readiness["version"] == HELPUSAI_FINAL_VERSION == "v0.29.0-dev"
    assert readiness["ready_for_release"] is False
    assert "git diff --check" in readiness["required_smokes"]
    assert "npm --prefix frontend run build" in readiness["required_smokes"]
    assert any("patch proposal" in gate for gate in readiness["safety_gates"])
    assert any("deploy only after explicit human approval" in step for step in readiness["remaining_manual_steps"])
    assert len(REQUIRED_FINAL_SMOKES) >= 20

if __name__ == "__main__":
    test_final_release_readiness()
    print("OK smoke_helpus_final_release_readiness")
