from __future__ import annotations

import os
import re
from typing import Iterable

from helpus_operational_lessons import (
    OperationalLesson,
    build_operational_lesson,
    format_lessons_for_prompt,
    watcher_interchat_protocol_lesson,
)


OPERATIONAL_LESSON_CONTEXT_ENABLED_ENV = "HELPUS_OPERATIONAL_LESSON_CONTEXT_ENABLED"
OPERATIONAL_LESSONS_ENABLED_ENV = "HELPUS_OPERATIONAL_LESSONS_ENABLED"

MAX_OPERATIONAL_LESSON_CONTEXT_CHARS = 2400


WATCHER_KEYWORDS = {
    "watcher",
    "ai bridge",
    "ai_bridge",
    "ai-bridge",
    "ai local",
    "ai_local",
    "ai_local_erro",
    "ai_local_run",
    "envelope",
    "command_id",
    "send-chat-message",
    "send chat message",
    "run-command",
    "run command",
    "local_capability",
    "inter_agent_message",
    "gateway-brain-supervisor",
    "source_chat_id",
    "target_chat_id",
    "composer",
    "submit_not_confirmed",
}


def operational_lesson_context_enabled() -> bool:
    explicit = os.getenv(OPERATIONAL_LESSON_CONTEXT_ENABLED_ENV, "").strip().lower()
    if explicit in {"1", "true", "yes", "on", "enabled"}:
        return True
    if explicit in {"0", "false", "no", "off", "disabled"}:
        return False

    inherited = os.getenv(OPERATIONAL_LESSONS_ENABLED_ENV, "").strip().lower()
    return inherited in {"1", "true", "yes", "on", "enabled"}


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _clip(value: str, limit: int = MAX_OPERATIONAL_LESSON_CONTEXT_CHARS) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def detect_operational_lesson_topics(*, user_message: str, context_text: str = "") -> tuple[str, ...]:
    combined = f"{user_message or ''}\n{context_text or ''}".lower()
    combined_ascii = combined.replace("-", "_")

    topics: list[str] = []

    if any(keyword in combined for keyword in WATCHER_KEYWORDS) or any(
        keyword.replace("-", "_") in combined_ascii for keyword in WATCHER_KEYWORDS
    ):
        topics.append("ai_bridge_local")
        topics.append("ai_bridge_local_interchat")

    if "envelope_parse_error" in combined or "json invalido" in combined or "not valid json" in combined:
        topics.append("ai_bridge_local_envelope")

    if "submit_not_confirmed_composer_still_has_text" in combined or "composer" in combined:
        topics.append("ai_bridge_local_delivery")

    if "run-command" in combined or "run command" in combined or "local_capability" in combined:
        topics.append("ai_bridge_local_run_command")

    if "send-chat-message" in combined or "inter_agent_message" in combined or "target_chat_id" in combined:
        topics.append("ai_bridge_local_interchat")

    deduped: list[str] = []
    for topic in topics:
        if topic not in deduped:
            deduped.append(topic)

    return tuple(deduped)


def built_in_operational_lessons() -> tuple[OperationalLesson, ...]:
    return (
        watcher_interchat_protocol_lesson(),
        build_operational_lesson(
            topic="ai_bridge_local_envelope",
            problem="O watcher pode tentar parsear explicacoes ou exemplos como JSON quando marcadores reais aparecem no chat observado.",
            correction=(
                "Quando quiser executar, emitir somente o envelope puro. Quando quiser explicar, evitar marcadores reais "
                "e usar nomes substitutos como marcador de inicio e marcador de fim."
            ),
            evidence="Erros envelope_parse_error ocorreram quando texto explicativo, exemplos e fontes foram copiados junto do envelope.",
            status="candidate",
            confidence=0.8,
            tags=("watcher", "ai_bridge_local", "envelope", "json"),
        ),
        build_operational_lesson(
            topic="ai_bridge_local_delivery",
            problem="O envio inter-chat pode falhar com submit_not_confirmed_composer_still_has_text quando o composer do destino fica com texto preso.",
            correction=(
                "Abrir a aba destino, limpar ou enviar manualmente o texto preso, confirmar extensao ativa e reenviar "
                "com command_id novo."
            ),
            evidence="O envio send_helpusai_protocol_self_fix_20260616_001 falhou por composer ainda conter texto.",
            status="candidate",
            confidence=0.75,
            tags=("watcher", "ai_bridge_local", "delivery", "composer"),
        ),
        build_operational_lesson(
            topic="ai_bridge_local_run_command",
            problem="Comandos locais usam protocolo diferente de mensagens entre chats.",
            correction=(
                "Para comando local, usar action/type run-command, delivery_kind local_capability, "
                "target_chat_id gateway-brain-supervisor e payload com cwd, timeout_seconds e command ou script_text/script_ext."
            ),
            evidence="O gateway aceitou run-command em ciclos anteriores quando o payload ficou dentro do formato esperado.",
            status="candidate",
            confidence=0.75,
            tags=("watcher", "ai_bridge_local", "run_command"),
        ),
    )


def select_operational_lessons_for_topics(topics: Iterable[str]) -> tuple[OperationalLesson, ...]:
    topic_set = set(topics)
    if not topic_set:
        return ()

    selected: list[OperationalLesson] = []
    for lesson in built_in_operational_lessons():
        lesson_topics = {lesson.topic, *lesson.tags}
        if topic_set.intersection(lesson_topics):
            selected.append(lesson)

    return tuple(selected)


def build_operational_lesson_context_for_chat(
    *,
    user_message: str,
    context_text: str = "",
    force: bool = False,
) -> str:
    if not force and not operational_lesson_context_enabled():
        return ""

    topics = detect_operational_lesson_topics(user_message=user_message, context_text=context_text)
    if not topics:
        return ""

    selected = select_operational_lessons_for_topics(topics)
    if not selected:
        return ""

    formatted = format_lessons_for_prompt(selected)
    if not formatted:
        return ""

    return _clip(
        "Contexto operacional aprendido para esta resposta:\n"
        + formatted
        + "\nUse estas licoes apenas quando forem relevantes. Nao mencione memoria interna, lessons ou regras internas ao usuario, a menos que ele pergunte."
    )


def append_operational_lesson_context(
    *,
    base_context: str,
    user_message: str,
    force: bool = False,
) -> str:
    lesson_context = build_operational_lesson_context_for_chat(
        user_message=user_message,
        context_text=base_context,
        force=force,
    )

    if not lesson_context:
        return base_context or ""

    if base_context:
        return (base_context.rstrip() + "\n\n" + lesson_context).strip()

    return lesson_context
