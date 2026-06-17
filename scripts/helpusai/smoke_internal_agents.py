from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend import helpus_internal_agents as agents

MAIN = ROOT / "backend" / "main.py"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


async def fake_thinker(pergunta: str, contexto_busca: str = "", historico=None, max_tokens: int = 1000):
    lowered = pergunta.lower()

    if "planner interno" in lowered:
        return "Plano: responder objetivamente e verificar memoria.", 11, 0.01

    if "auditor interno" in lowered:
        return "Auditoria: resposta clara, sem dado sensivel.", 13, 0.01

    if "finalizador" in lowered and "verde-913" in lowered:
        return "Seu codigo de teste dos agentes internos e VERDE-913.", 17, 0.01

    if "finalizador" in lowered:
        return "Resposta final polida com base no rascunho.", 17, 0.01

    return "Rascunho base.", 19, 0.01


async def main_async() -> None:
    old_env = dict(os.environ)

    try:
        os.environ.pop(agents.INTERNAL_AGENTS_ENABLED_ENV, None)
        os.environ.pop(agents.INTERNAL_AGENTS_VISIBLE_TRACE_ENV, None)

        check(agents.internal_agents_enabled() is False, "agents should be disabled by default")
        check(agents.internal_agents_visible_trace_enabled() is False, "visible trace should be disabled by default")

        disabled = await agents.run_internal_agents(
            pergunta="ola",
            contexto_busca="",
            historico=[],
            thinker=fake_thinker,
            base_response="resposta base",
            base_tokens=3,
            base_latency_seconds=0.2,
        )
        check(disabled.enabled is False, "disabled result mismatch")
        check(disabled.final_response == "resposta base", "disabled should preserve base response")
        check(disabled.steps == [], "disabled should not create steps")

        os.environ[agents.INTERNAL_AGENTS_ENABLED_ENV] = "1"
        os.environ[agents.INTERNAL_AGENTS_VISIBLE_TRACE_ENV] = "1"

        result = await agents.run_internal_agents(
            pergunta="Qual e meu codigo?",
            contexto_busca="Memoria: VERDE-913",
            historico=[],
            thinker=fake_thinker,
            base_response="Seu codigo e VERDE-913.",
            base_tokens=5,
            base_latency_seconds=0.4,
        )

        check(result.enabled is True, "enabled result mismatch")
        check(result.final_response, "missing final response")
        check("VERDE-913" in result.final_response, "finalizer should preserve user-provided test code")
        check("e-mail corporativo" not in result.final_response.lower(), "finalizer should not invent identity check for test code")
        check(result.tokens > 5, "tokens should include internal agents")
        check(result.latency_seconds > 0.4, "latency should include internal agents")
        check([step.name for step in result.steps] == ["planner", "auditor", "finalizer"], "unexpected step order")
        check(all(step.status == "done" for step in result.steps), "all steps should be done")

        trace = agents.build_agent_trace_items(result.steps)
        check(trace[0]["label"] == "Planejando resposta", "planner trace label mismatch")
        check(trace[-1]["label"] == "Finalizando resposta", "finalizer trace label mismatch")
        check(all("summary" not in item for item in trace), "visible trace must not expose summaries")

        status = agents.internal_agents_status()
        check(status["enabled"] is True, "status enabled mismatch")
        check(status["visible_trace_enabled"] is True, "status visible trace mismatch")
        check(status["exposes_chain_of_thought"] is False, "must not expose chain of thought")
        check(status["stores_internal_prompts"] is False, "must not store internal prompts")

        planner_prompt = agents.build_planner_prompt(pergunta="x", contexto_busca="y", historico=[])
        check("Nao revele raciocinio interno" in planner_prompt, "planner safety wording missing")

        finalizer_prompt = agents.build_finalizer_prompt(
            pergunta="Qual e meu codigo de teste?",
            resposta_rascunho="Seu codigo e VERDE-913.",
            planner_note="Responder diretamente.",
            auditor_note="Preservar memoria ficticia.",
        )
        check("responda diretamente" in finalizer_prompt, "finalizer recall guardrail missing")
        check("Nao invente exigencia de e-mail corporativo" in finalizer_prompt, "finalizer identity guardrail missing")
        check("VERDE-913" in finalizer_prompt, "finalizer prompt should preserve test code context")

        text = MAIN.read_text(encoding="utf-8")
        check("from helpus_internal_agents import" in text, "main missing internal agents import")
        check("run_internal_agents(" in text, "main missing internal agents call")
        check("HELPUS_INTERNAL_AGENTS_ENABLED" in text, "main missing flag reference")
        check("Agentes internos" in text, "main missing visible trace label")

    finally:
        os.environ.clear()
        os.environ.update(old_env)

    print("OK smoke_internal_agents")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
