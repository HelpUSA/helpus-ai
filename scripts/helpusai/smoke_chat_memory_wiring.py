from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MAIN = ROOT / "backend" / "main.py"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    text = MAIN.read_text(encoding="utf-8")

    check(
        "from starlette.concurrency import run_in_threadpool" in text,
        "missing run_in_threadpool import",
    )
    check(
        "from helpus_internal_memory_recorder import safe_record_chat_memory_event" in text,
        "missing safe_record_chat_memory_event import",
    )
    check(
        "# Grava evento de memoria interna sem afetar a resposta do chat." in text,
        "missing recorder block comment",
    )
    check(
        "await run_in_threadpool(" in text,
        "missing threadpool call",
    )
    check(
        "safe_record_chat_memory_event," in text,
        "missing recorder callable in threadpool",
    )
    check(
        "user_message=request.mensagem" in text,
        "missing user_message mapping",
    )
    check(
        "assistant_reply=resposta" in text,
        "missing assistant_reply mapping",
    )
    check(
        "conversation_id=session_id" in text,
        "missing conversation_id mapping",
    )
    check(
        "actor=\"assistant\"" in text,
        "missing actor mapping",
    )
    check(
        "route=\"chat\"" in text,
        "missing route mapping",
    )
    check(
        "project_id=project_id" in text,
        "missing project_id mapping",
    )
    check(
        "\"tokens_gerados\": tokens" in text,
        "missing tokens metadata",
    )
    check(
        "\"tempo_ia\": tempo_ia" in text,
        "missing tempo_ia metadata",
    )
    check(
        "\"fontes_count\": len(fontes)" in text,
        "missing fontes_count metadata",
    )

    response_idx = text.index("resposta, tokens, tempo_ia = await cerebro.pensar")
    record_idx = text.index("# Grava evento de memoria interna sem afetar a resposta do chat.")
    return_idx = text.index("return MensagemResponse(")

    check(
        response_idx < record_idx < return_idx,
        "recorder block must happen after AI response and before MensagemResponse return",
    )

    tree = ast.parse(text)
    chat_functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "chat"
    ]
    check(len(chat_functions) == 1, "expected exactly one chat function")

    print("OK smoke_chat_memory_wiring")


if __name__ == "__main__":
    main()
