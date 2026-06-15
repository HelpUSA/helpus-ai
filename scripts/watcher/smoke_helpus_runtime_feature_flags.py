from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_runtime_feature_flags import ADAPTER_ENABLED_FLAG, ADAPTER_FORCE_FLAG, load_helpus_runtime_feature_flags, parse_bool

def test_parse_bool() -> None:
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool("on") is True
    assert parse_bool("false") is False
    assert parse_bool("0") is False
    assert parse_bool(None) is False
    assert parse_bool("weird", default=True) is True

def test_flags_default_disabled() -> None:
    data = load_helpus_runtime_feature_flags({}).to_dict()
    assert data["conversation_adapter_enabled"] is False
    assert data["conversation_adapter_force"] is False
    assert data["adapter_enabled_flag"] == ADAPTER_ENABLED_FLAG
    assert data["adapter_force_flag"] == ADAPTER_FORCE_FLAG
    assert data["default_enabled"] is False

def test_flags_enabled() -> None:
    flags = load_helpus_runtime_feature_flags({ADAPTER_ENABLED_FLAG: "true", ADAPTER_FORCE_FLAG: "yes"})
    assert flags.conversation_adapter_enabled is True
    assert flags.conversation_adapter_force is True

if __name__ == "__main__":
    test_parse_bool()
    test_flags_default_disabled()
    test_flags_enabled()
    print("OK smoke_helpus_runtime_feature_flags")
