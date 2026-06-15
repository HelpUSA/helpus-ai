from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_operator_visibility import build_helpus_operator_visibility
from backend.helpus_runtime_feature_flags import ADAPTER_ENABLED_FLAG

def test_operator_visibility_default() -> None:
    status = build_helpus_operator_visibility({})
    assert status["version"] == "v0.22.0-dev"
    assert status["latest_micro"] == "Micro 22 - operator visibility status"
    assert status["feature_flags"]["conversation_adapter_enabled"] is False
    assert status["safety"]["adapter_default_enabled"] is False
    assert status["safety"]["executes_commands"] is False
    assert any("Micro 19" in item for item in status["chain"])
    assert any("Micro 22" in item for item in status["chain"])

def test_operator_visibility_enabled_flag_visible() -> None:
    status = build_helpus_operator_visibility({ADAPTER_ENABLED_FLAG: "true"})
    assert status["feature_flags"]["conversation_adapter_enabled"] is True

if __name__ == "__main__":
    test_operator_visibility_default()
    test_operator_visibility_enabled_flag_visible()
    print("OK smoke_helpus_operator_visibility")
