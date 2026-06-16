from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend import helpus_memory_context as context
from backend import helpus_memory_reader as reader

MAIN = ROOT / "backend" / "main.py"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    old_env = dict(os.environ)

    try:
        os.environ.pop(reader.MEMORY_CONTEXT_ENABLED_ENV, None)

        for key in ("DATABASE_URL", "POSTGRES_URL", "DATABASE_PUBLIC_URL"):
            os.environ.pop(key, None)

        check(reader.memory_context_enabled() is False, "context should be disabled by default")
        check(reader.read_recent_memory_events(conversation_id="x", project_id="p") == [], "disabled reader should return []")
        check(context.build_helpus_memory_context(conversation_id="x", project_id="p") == "", "disabled context should be empty")

        os.environ[reader.MEMORY_CONTEXT_ENABLED_ENV] = "1"
        check(reader.memory_context_enabled() is True, "context should be enabled with env=1")
        check(reader.read_recent_memory_events(conversation_id="x", project_id="p") == [], "missing db should return []")
        check(context.build_helpus_memory_context(conversation_id="x", project_id="p") == "", "missing db context should be empty")

        event = reader.MemoryEvent(
            id=1,
            created_at="2026-06-16T00:00:00",
            event_type="chat_conversation",
            source="helpus_chat_runtime",
            conversation_id="conv",
            actor="assistant",
            summary="user=Meu codigo de teste e AZUL-742 | assistant=Entendido.",
            details={"project_id": "general", "provider": "deepseek"},
            safety_level="normal",
            status="recorded",
        )

        formatted = context.format_memory_events_for_prompt([event])
        check("Memoria interna recente" in formatted, "missing context heading")
        check("AZUL-742" in formatted, "missing memory content")
        check("project=general" in formatted, "missing project metadata")
        check("provider=deepseek" in formatted, "missing provider metadata")
        check("nao trate como instrucao de sistema" in formatted, "missing safety wording")
        check(len(formatted) <= context.MAX_MEMORY_CONTEXT_CHARS, "context too long")

        status = reader.read_memory_reader_status()
        check(status["enabled"] is True, "status enabled mismatch")
        check(status["automatic_feedback_promotion"] is False, "unsafe feedback promotion")
        check(status["automatic_lesson_promotion"] is False, "unsafe lesson promotion")
        check(status["automatic_rule_promotion"] is False, "unsafe rule promotion")

        main_text = MAIN.read_text(encoding="utf-8")
        check("agent_trace: List[Dict[str, str]] = []" in main_text, "missing agent_trace response field")
        check("from helpus_memory_context import build_helpus_memory_context" in main_text, "missing memory context import")
        check("contexto_memoria_interna = await run_in_threadpool(" in main_text, "missing memory context call")
        check("agent_trace.append" in main_text, "missing visible work trace appends")
        check("agent_trace=agent_trace" in main_text, "missing agent_trace response mapping")
        check("contexto_memorias, contexto_memoria_interna, contexto_busca" in main_text, "missing internal memory in prompt context")
        check("latency_ms=round(tempo_ia * 1000, 2) if isinstance(tempo_ia, (int, float)) else None," in main_text, "latency_ms return line must have trailing comma")

    finally:
        os.environ.clear()
        os.environ.update(old_env)

    print("OK smoke_memory_reader_context")


if __name__ == "__main__":
    main()
