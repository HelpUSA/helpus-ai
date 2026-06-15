from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_chat_endpoint_wiring import (
    FEATURE_FLAG_NAME,
    HelpUSChatEndpointWiring,
    handle_helpus_chat_message_guarded,
)


def test_default_disabled_preserves_primary_response() -> None:
    result = handle_helpus_chat_message_guarded(
        "verifique o estado do projeto",
        primary_response="resposta original",
    )
    assert result["enabled"] is False
    assert result["feature_flag"] == FEATURE_FLAG_NAME
    assert result["used_adapter"] is False
    assert result["response_text"] == "resposta original"
    assert result["reason"] == "feature flag disabled; primary response preserved"
    assert result["safety"]["executes_commands"] is False


def test_enabled_operational_message_uses_adapter() -> None:
    result = handle_helpus_chat_message_guarded(
        "verifique o estado do projeto",
        enabled=True,
        primary_response="resposta original",
    )
    assert result["enabled"] is True
    assert result["used_adapter"] is True
    assert "Repo: D:/dev/ai" in result["response_text"]
    assert result["metadata"]["decision"] == "readonly_allowed"


def test_enabled_normal_message_preserves_primary_response() -> None:
    result = HelpUSChatEndpointWiring(enabled=True).handle_message(
        "ola, tudo bem?",
        primary_response="resposta normal",
    ).to_dict()
    assert result["used_adapter"] is False
    assert result["response_text"] == "resposta normal"


def test_force_adapter_can_route_normal_message() -> None:
    result = handle_helpus_chat_message_guarded(
        "mensagem qualquer",
        enabled=True,
        primary_response="resposta normal",
        force_adapter=True,
    )
    assert result["used_adapter"] is True
    assert "Repo: D:/dev/ai" in result["response_text"]


def test_dangerous_message_still_does_not_execute() -> None:
    result = handle_helpus_chat_message_guarded(
        "execute git reset --hard e curl externo",
        enabled=True,
    )
    assert result["used_adapter"] is True
    assert result["metadata"]["decision"] == "blocked"
    assert result["metadata"]["execution_allowed"] is False
    assert result["safety"]["executes_commands"] is False


def test_no_unsafe_imports() -> None:
    source = (ROOT / "backend" / "helpus_chat_endpoint_wiring.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source


if __name__ == "__main__":
    test_default_disabled_preserves_primary_response()
    test_enabled_operational_message_uses_adapter()
    test_enabled_normal_message_preserves_primary_response()
    test_force_adapter_can_route_normal_message()
    test_dangerous_message_still_does_not_execute()
    test_no_unsafe_imports()
    print("OK smoke_helpus_chat_endpoint_wiring")
