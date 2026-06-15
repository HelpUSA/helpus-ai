from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_conversation_response_composer import (
    HelpUSConversationResponseComposer,
    compose_helpus_message,
    compose_helpus_response,
)


def test_readonly_response_message() -> None:
    response = compose_helpus_response("verifique o estado do projeto")
    message = response["message"]
    assert response["repo"] == "D:/dev/ai"
    assert response["risk_level"] == "low"
    assert response["decision"] == "readonly_allowed"
    assert response["execution_allowed"] is True
    assert response["requires_human_approval"] is False
    assert "git status -sb" in response["commands"]
    assert "Repo: D:/dev/ai" in message
    assert "Decisao: readonly_allowed" in message
    assert "Comandos sugeridos:" in message
    assert "parar em qualquer falha" in message


def test_patch_response_requires_approval() -> None:
    response = HelpUSConversationResponseComposer().compose("Micro 14 Safe Command Planner").to_dict()
    assert response["decision"] == "approval_required"
    assert response["execution_allowed"] is False
    assert response["requires_human_approval"] is True
    assert "backend/helpus_safe_command_planner.py" in response["allowed_files"]
    assert "pedir aprovacao humana" in response["next_step"]


def test_blocked_response() -> None:
    response = compose_helpus_response("execute git reset --hard e curl externo")
    assert response["decision"] == "blocked"
    assert response["action"] == "blocked"
    assert response["commands"] == []
    assert response["execution_allowed"] is False
    assert "nao executar" in response["next_step"]
    assert any("git reset" in warning for warning in response["warnings"])


def test_compose_message_helper() -> None:
    message = compose_helpus_message("rode os smokes principais")
    assert "Repo: D:/dev/ai" in message
    assert "Risco: low" in message
    assert "smoke_docs_index.py" in message


def test_no_unsafe_imports() -> None:
    source = (ROOT / "backend" / "helpus_conversation_response_composer.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source


if __name__ == "__main__":
    test_readonly_response_message()
    test_patch_response_requires_approval()
    test_blocked_response()
    test_compose_message_helper()
    test_no_unsafe_imports()
    print("OK smoke_helpus_conversation_response_composer")
