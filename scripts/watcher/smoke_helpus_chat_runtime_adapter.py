from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_chat_runtime_adapter import handle_helpus_runtime_chat_message
from backend.helpus_runtime_feature_flags import ADAPTER_ENABLED_FLAG, ADAPTER_FORCE_FLAG

def test_default_disabled_preserves_primary_response() -> None:
    result = handle_helpus_runtime_chat_message("verifique o estado do projeto", primary_response="resposta principal", env={})
    assert result["enabled"] is False
    assert result["used_adapter"] is False
    assert result["response_text"] == "resposta principal"
    assert result["metadata"]["feature_flags"]["conversation_adapter_enabled"] is False

def test_enabled_operational_message_uses_adapter() -> None:
    result = handle_helpus_runtime_chat_message("verifique o estado do projeto", primary_response="resposta principal", env={ADAPTER_ENABLED_FLAG: "true"})
    assert result["enabled"] is True
    assert result["used_adapter"] is True
    assert "Repo: D:/dev/ai" in result["response_text"]
    assert result["metadata"]["decision"] == "readonly_allowed"

def test_force_adapter_for_normal_message() -> None:
    result = handle_helpus_runtime_chat_message("mensagem qualquer", primary_response="resposta principal", env={ADAPTER_ENABLED_FLAG: "true", ADAPTER_FORCE_FLAG: "true"})
    assert result["enabled"] is True
    assert result["used_adapter"] is True
    assert "Repo: D:/dev/ai" in result["response_text"]

def test_no_unsafe_imports() -> None:
    source = (ROOT / "backend" / "helpus_chat_runtime_adapter.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source

if __name__ == "__main__":
    test_default_disabled_preserves_primary_response()
    test_enabled_operational_message_uses_adapter()
    test_force_adapter_for_normal_message()
    test_no_unsafe_imports()
    print("OK smoke_helpus_chat_runtime_adapter")
