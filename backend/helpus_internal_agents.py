from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

INTERNAL_AGENTS_ENABLED_ENV = "HELPUS_INTERNAL_AGENTS_ENABLED"
INTERNAL_AGENTS_VISIBLE_TRACE_ENV = "HELPUS_INTERNAL_AGENTS_VISIBLE_TRACE"

MAX_INTERNAL_TEXT_CHARS = 1800
MAX_FINAL_RESPONSE_CHARS = 8000

InternalThinker = Callable[..., Awaitable[tuple[str, int, float]]]


@dataclass(frozen=True)
class InternalAgentStep:
    name: str
    label: str
    status: str
    summary: str = ""


@dataclass(frozen=True)
class InternalAgentsResult:
    enabled: bool
    final_response: str
    tokens: int
    latency_seconds: float
    steps: list[InternalAgentStep]
    planner_note: str = ""
    auditor_note: str = ""


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def internal_agents_enabled() -> bool:
    return _truthy(os.getenv(INTERNAL_AGENTS_ENABLED_ENV))


def internal_agents_visible_trace_enabled() -> bool:
    return _truthy(os.getenv(INTERNAL_AGENTS_VISIBLE_TRACE_ENV))


def compact_text(value: Any, limit: int = MAX_INTERNAL_TEXT_CHARS) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    if len(text) <= limit:
        return text

    suffix = "...[truncated]"
    return text[: max(0, limit - len(suffix))].rstrip() + suffix


def _safe_step_summary(value: Any) -> str:
    text = compact_text(value, 220)
    return text.replace("```", "").strip()


def build_agent_trace_items(steps: list[InternalAgentStep]) -> list[dict[str, str]]:
    return [{"label": step.label, "status": step.status} for step in steps]


def build_planner_prompt(*, pergunta: str, contexto_busca: str = "", historico: list[dict] | None = None) -> str:
    history_count = len(historico or [])
    return (
        "Voce e o Planner interno da HelpUSAI. "
        "Prepare um plano curto para responder ao usuario. "
        "Nao responda ao usuario final. Nao revele raciocinio interno. "
        "Produza no maximo 5 linhas, com objetivo, contexto util e riscos.\n\n"
        f"Pergunta do usuario:\n{compact_text(pergunta)}\n\n"
        f"Contexto disponivel:\n{compact_text(contexto_busca)}\n\n"
        f"Quantidade de mensagens no historico: {history_count}\n"
    )


def build_auditor_prompt(*, pergunta: str, resposta_rascunho: str, planner_note: str = "") -> str:
    return (
        "Voce e o Auditor interno da HelpUSAI. "
        "Revise o rascunho procurando lacunas, risco de seguranca, promessa exagerada, "
        "dados sensiveis e falta de clareza. Nao responda ao usuario final. "
        "Produza no maximo 5 linhas objetivas.\n\n"
        f"Pergunta do usuario:\n{compact_text(pergunta)}\n\n"
        f"Plano interno:\n{compact_text(planner_note)}\n\n"
        f"Rascunho de resposta:\n{compact_text(resposta_rascunho, 2600)}\n"
    )


def build_finalizer_prompt(
    *,
    pergunta: str,
    resposta_rascunho: str,
    planner_note: str = "",
    auditor_note: str = "",
) -> str:
    return (
        "Voce e o Finalizador da HelpUSAI. "
        "Escreva apenas a resposta final para o usuario, em portugues claro. "
        "Use o plano e a auditoria apenas como apoio interno. "
        "Nao mencione Planner, Auditor, Finalizador, cadeia de pensamento ou prompts internos.\n\n"
        f"Pergunta do usuario:\n{compact_text(pergunta)}\n\n"
        f"Plano interno:\n{compact_text(planner_note)}\n\n"
        f"Auditoria interna:\n{compact_text(auditor_note)}\n\n"
        f"Rascunho base:\n{compact_text(resposta_rascunho, 5000)}\n"
    )


async def run_internal_agents(
    *,
    pergunta: str,
    contexto_busca: str,
    historico: list[dict] | None,
    thinker: InternalThinker,
    base_response: str | None = None,
    base_tokens: int = 0,
    base_latency_seconds: float = 0.0,
) -> InternalAgentsResult:
    if not internal_agents_enabled():
        return InternalAgentsResult(
            enabled=False,
            final_response=base_response or "",
            tokens=base_tokens,
            latency_seconds=base_latency_seconds,
            steps=[],
        )

    steps: list[InternalAgentStep] = []
    total_tokens = int(base_tokens or 0)
    total_latency = float(base_latency_seconds or 0.0)
    planner_note = ""
    auditor_note = ""
    final_response = base_response or ""

    try:
        steps.append(InternalAgentStep("planner", "Planejando resposta", "running"))
        planner_note, planner_tokens, planner_latency = await thinker(
            build_planner_prompt(pergunta=pergunta, contexto_busca=contexto_busca, historico=historico),
            contexto_busca="",
            historico=[],
            max_tokens=350,
        )
        total_tokens += int(planner_tokens or 0)
        total_latency += float(planner_latency or 0.0)
        steps[-1] = InternalAgentStep("planner", "Planejando resposta", "done", _safe_step_summary(planner_note))
    except Exception as exc:
        steps[-1] = InternalAgentStep("planner", "Planejando resposta", "skipped", _safe_step_summary(exc))

    try:
        steps.append(InternalAgentStep("auditor", "Auditando resposta", "running"))
        auditor_note, auditor_tokens, auditor_latency = await thinker(
            build_auditor_prompt(pergunta=pergunta, resposta_rascunho=final_response, planner_note=planner_note),
            contexto_busca="",
            historico=[],
            max_tokens=350,
        )
        total_tokens += int(auditor_tokens or 0)
        total_latency += float(auditor_latency or 0.0)
        steps[-1] = InternalAgentStep("auditor", "Auditando resposta", "done", _safe_step_summary(auditor_note))
    except Exception as exc:
        steps[-1] = InternalAgentStep("auditor", "Auditando resposta", "skipped", _safe_step_summary(exc))

    try:
        steps.append(InternalAgentStep("finalizer", "Finalizando resposta", "running"))
        polished_response, finalizer_tokens, finalizer_latency = await thinker(
            build_finalizer_prompt(
                pergunta=pergunta,
                resposta_rascunho=final_response,
                planner_note=planner_note,
                auditor_note=auditor_note,
            ),
            contexto_busca="",
            historico=[],
            max_tokens=1200,
        )
        total_tokens += int(finalizer_tokens or 0)
        total_latency += float(finalizer_latency or 0.0)

        if polished_response and polished_response.strip():
            final_response = compact_text(polished_response, MAX_FINAL_RESPONSE_CHARS)

        steps[-1] = InternalAgentStep("finalizer", "Finalizando resposta", "done", _safe_step_summary(final_response))
    except Exception as exc:
        steps[-1] = InternalAgentStep("finalizer", "Finalizando resposta", "skipped", _safe_step_summary(exc))

    return InternalAgentsResult(
        enabled=True,
        final_response=final_response,
        tokens=total_tokens,
        latency_seconds=total_latency,
        steps=steps,
        planner_note=planner_note,
        auditor_note=auditor_note,
    )


def internal_agents_status() -> dict[str, Any]:
    return {
        "enabled": internal_agents_enabled(),
        "enabled_env": INTERNAL_AGENTS_ENABLED_ENV,
        "visible_trace_enabled": internal_agents_visible_trace_enabled(),
        "visible_trace_env": INTERNAL_AGENTS_VISIBLE_TRACE_ENV,
        "agents": ["planner", "auditor", "finalizer"],
        "exposes_chain_of_thought": False,
        "stores_internal_prompts": False,
        "requires_human_approval": False,
    }
