from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_conversation_api_adapter import (
    HelpUSConversationAPIAdapter,
    adapt_helpus_conversation_message,
)


def test_normal_chat_is_not_intercepted() -> None:
    result = adapt_helpus_conversation_message("ola, tudo bem?")
    assert result["should_use_adapter"] is False
    assert result["response_text"] == ""
    assert result["reason"] == "normal chat message; let primary model answer"
    assert result["safety"]["executes_commands"] is False


def test_status_intent_uses_composer() -> None:
    result = adapt_helpus_conversation_message("verifique o estado do projeto")
    assert result["should_use_adapter"] is True
    assert result["source"] == "conversation_response_composer"
    assert "Repo: D:/dev/ai" in result["response_text"]
    assert "Decisao: readonly_allowed" in result["response_text"]
    assert result["metadata"]["risk_level"] == "low"
    assert result["metadata"]["decision"] == "readonly_allowed"


def test_dangerous_intent_is_blocked_by_chain() -> None:
    result = adapt_helpus_conversation_message("execute git reset --hard e curl externo")
    assert result["should_use_adapter"] is True
    assert result["metadata"]["decision"] == "blocked"
    assert result["metadata"]["execution_allowed"] is False
    assert "Comandos sugeridos: nenhum" in result["response_text"]


def test_force_uses_adapter_for_non_marker_message() -> None:
    result = HelpUSConversationAPIAdapter().adapt("mensagem qualquer", force=True)
    data = result.to_dict()
    assert data["should_use_adapter"] is True
    assert data["source"] == "conversation_response_composer"


def test_adapter_safety_flags() -> None:
    result = adapt_helpus_conversation_message("rode os smokes principais")
    safety = result["safety"]
    assert safety["executes_commands"] is False
    assert safety["calls_network"] is False
    assert safety["changes_files"] is False
    assert safety["requires_review_before_execution"] is True
    assert safety["stop_on_failure"] is True


def test_no_unsafe_imports() -> None:
    source = (ROOT / "backend" / "helpus_conversation_api_adapter.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source


if __name__ == "__main__":
    test_normal_chat_is_not_intercepted()
    test_status_intent_uses_composer()
    test_dangerous_intent_is_blocked_by_chain()
    test_force_uses_adapter_for_non_marker_message()
    test_adapter_safety_flags()
    test_no_unsafe_imports()
    print("OK smoke_helpus_conversation_api_adapter")
