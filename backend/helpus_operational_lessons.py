from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


OPERATIONAL_LESSON_SOURCE = "helpus_operational_lessons"
OPERATIONAL_LESSON_PROJECT_ID = "helpusai"
OPERATIONAL_LESSON_DEFAULT_STATUS = "candidate"

MAX_TOPIC_LENGTH = 96
MAX_PROBLEM_LENGTH = 500
MAX_CORRECTION_LENGTH = 900
MAX_EVIDENCE_LENGTH = 900
MAX_LESSONS_FOR_PROMPT = 8

LESSON_MEMORY_ENABLED_ENV = "HELPUS_OPERATIONAL_LESSONS_ENABLED"


@dataclass(frozen=True)
class OperationalLesson:
    topic: str
    problem: str
    correction: str
    evidence: str = ""
    status: str = OPERATIONAL_LESSON_DEFAULT_STATUS
    source: str = OPERATIONAL_LESSON_SOURCE
    confidence: float = 0.5
    tags: tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = list(self.tags)
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)


@dataclass(frozen=True)
class OperationalLessonRecordResult:
    status: str
    enabled: bool
    reason: str = ""
    lesson: OperationalLesson | None = None
    recorder_status: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "enabled": self.enabled,
            "reason": self.reason,
            "lesson": self.lesson.to_dict() if self.lesson else None,
            "recorder_status": self.recorder_status,
        }


def operational_lessons_enabled() -> bool:
    value = os.getenv(LESSON_MEMORY_ENABLED_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on", "enabled"}


def _collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _clip(value: str, limit: int) -> str:
    value = _collapse_spaces(value)
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def _normalize_topic(topic: str) -> str:
    topic = _collapse_spaces(topic).lower()
    topic = re.sub(r"[^a-z0-9_\-:.]+", "_", topic)
    topic = topic.strip("_")
    return _clip(topic or "general", MAX_TOPIC_LENGTH)


def _normalize_tags(tags: Iterable[str] | None) -> tuple[str, ...]:
    if not tags:
        return ()

    normalized: list[str] = []
    for tag in tags:
        clean = _normalize_topic(str(tag))
        if clean and clean not in normalized:
            normalized.append(clean)

    return tuple(normalized[:12])


def build_operational_lesson(
    *,
    topic: str,
    problem: str,
    correction: str,
    evidence: str = "",
    status: str = OPERATIONAL_LESSON_DEFAULT_STATUS,
    confidence: float = 0.5,
    tags: Iterable[str] | None = None,
) -> OperationalLesson:
    normalized_status = _collapse_spaces(status).lower() or OPERATIONAL_LESSON_DEFAULT_STATUS
    if normalized_status not in {"candidate", "promoted", "rejected"}:
        normalized_status = OPERATIONAL_LESSON_DEFAULT_STATUS

    try:
        normalized_confidence = float(confidence)
    except (TypeError, ValueError):
        normalized_confidence = 0.5

    normalized_confidence = max(0.0, min(1.0, normalized_confidence))

    return OperationalLesson(
        topic=_normalize_topic(topic),
        problem=_clip(problem, MAX_PROBLEM_LENGTH),
        correction=_clip(correction, MAX_CORRECTION_LENGTH),
        evidence=_clip(evidence, MAX_EVIDENCE_LENGTH),
        status=normalized_status,
        confidence=normalized_confidence,
        tags=_normalize_tags(tags),
    )


def build_lesson_summary(lesson: OperationalLesson) -> str:
    parts = [
        f"topic={lesson.topic}",
        f"status={lesson.status}",
        f"problem={lesson.problem}",
        f"correction={lesson.correction}",
    ]

    if lesson.evidence:
        parts.append(f"evidence={lesson.evidence}")

    if lesson.tags:
        parts.append("tags=" + ",".join(lesson.tags))

    return " | ".join(parts)


def build_lesson_memory_payload(lesson: OperationalLesson) -> dict[str, Any]:
    return {
        "kind": "operational_lesson",
        "source": lesson.source,
        "topic": lesson.topic,
        "status": lesson.status,
        "confidence": lesson.confidence,
        "tags": list(lesson.tags),
        "problem": lesson.problem,
        "correction": lesson.correction,
        "evidence": lesson.evidence,
        "created_at": lesson.created_at,
        "automatic_rule_promotion": False,
        "requires_validation_before_promotion": True,
    }


def format_lessons_for_prompt(lessons: Iterable[OperationalLesson], *, topic: str | None = None) -> str:
    filtered: list[OperationalLesson] = []

    normalized_topic = _normalize_topic(topic) if topic else ""

    for lesson in lessons:
        if normalized_topic and lesson.topic != normalized_topic and normalized_topic not in lesson.tags:
            continue
        filtered.append(lesson)

    filtered = filtered[:MAX_LESSONS_FOR_PROMPT]

    if not filtered:
        return ""

    lines = ["Licoes operacionais relevantes:"]
    for idx, lesson in enumerate(filtered, start=1):
        lines.append(
            f"{idx}. [{lesson.status}] {lesson.topic}: problema={lesson.problem}; correcao={lesson.correction}"
        )

    return "\n".join(lines)


def parse_ai_local_error_to_lesson(error_text: str, *, topic: str = "ai_bridge_local") -> OperationalLesson:
    text = error_text or ""
    lowered = text.lower()

    if "envelope_parse_error" in lowered:
        problem = "Envelope do AI Bridge Local falhou no parse por JSON invalido, texto extra ou marcadores/protocolo incorretos."
        correction = (
            "Emitir somente um envelope puro: marcadores reais sozinhos nas linhas, JSON estrito entre eles, "
            "command_id unico, sem explicacao antes/depois e campos corretos para a action desejada."
        )
        tags = ("watcher", "ai_bridge_local", "json", "envelope")
    elif "submit_not_confirmed_composer_still_has_text" in lowered:
        problem = "Mensagem foi injetada no composer do chat destino, mas o envio nao foi confirmado."
        correction = (
            "Verificar aba destino, limpar ou enviar texto preso no composer, garantir extensao ativa e reenviar com command_id novo."
        )
        tags = ("watcher", "ai_bridge_local", "delivery")
    elif "ai_local_run" in lowered and "success=0" in lowered:
        problem = "Comando local retornou falha no AI_LOCAL_RUN."
        correction = "Ler return_code, stdout e stderr; corrigir a causa menor dentro do mesmo escopo e rerodar validacoes."
        tags = ("watcher", "run_command", "failure")
    else:
        problem = "Evento operacional precisa ser revisado para extrair aprendizado."
        correction = "Resumir objetivo, erro, correcao aplicada, evidencia e proximo passo antes de promover regra."
        tags = ("operational_learning",)

    return build_operational_lesson(
        topic=topic,
        problem=problem,
        correction=correction,
        evidence=_clip(text, MAX_EVIDENCE_LENGTH),
        status="candidate",
        confidence=0.7,
        tags=tags,
    )


def record_operational_lesson_candidate(
    *,
    topic: str,
    problem: str,
    correction: str,
    evidence: str = "",
    confidence: float = 0.5,
    tags: Iterable[str] | None = None,
    conversation_id: str | None = None,
    provider: str = "internal",
) -> OperationalLessonRecordResult:
    lesson = build_operational_lesson(
        topic=topic,
        problem=problem,
        correction=correction,
        evidence=evidence,
        status="candidate",
        confidence=confidence,
        tags=tags,
    )

    if not operational_lessons_enabled():
        return OperationalLessonRecordResult(
            status="skipped",
            enabled=False,
            reason="operational_lessons_disabled",
            lesson=lesson,
        )

    try:
        from helpus_internal_memory_recorder import safe_record_chat_memory_event
    except Exception as exc:  # pragma: no cover - defensive import path guard
        return OperationalLessonRecordResult(
            status="skipped",
            enabled=True,
            reason=f"recorder_import_failed:{type(exc).__name__}",
            lesson=lesson,
        )

    payload = build_lesson_memory_payload(lesson)
    user_message = "Operational lesson candidate generated."
    assistant_reply = build_lesson_summary(lesson)

    result = safe_record_chat_memory_event(
        user_message=user_message,
        assistant_reply=assistant_reply,
        conversation_id=conversation_id or f"operational_lesson:{lesson.topic}",
        provider=provider,
        route="operational_lessons",
        project_id=OPERATIONAL_LESSON_PROJECT_ID,
        extra=payload,
    )

    return OperationalLessonRecordResult(
        status=getattr(result, "status", "unknown"),
        enabled=True,
        reason=getattr(result, "reason", ""),
        lesson=lesson,
        recorder_status=getattr(result, "status", "unknown"),
    )


def record_ai_local_error_lesson(
    error_text: str,
    *,
    topic: str = "ai_bridge_local",
    conversation_id: str | None = None,
) -> OperationalLessonRecordResult:
    lesson = parse_ai_local_error_to_lesson(error_text, topic=topic)
    return record_operational_lesson_candidate(
        topic=lesson.topic,
        problem=lesson.problem,
        correction=lesson.correction,
        evidence=lesson.evidence,
        confidence=lesson.confidence,
        tags=lesson.tags,
        conversation_id=conversation_id,
    )


def watcher_interchat_protocol_lesson() -> OperationalLesson:
    return build_operational_lesson(
        topic="ai_bridge_local_interchat",
        problem="A HelpUSAI confundiu o protocolo de envio entre chats e misturou explicacoes com envelope.",
        correction=(
            "Para mensagem entre chats, usar send-chat-message, delivery_kind inter_agent_message, "
            "source_chat_id, target_chat_id, message no topo, payload_json vazio e no_reply conforme necessario. "
            "O envelope deve sair sozinho, sem explicacao."
        ),
        evidence=(
            "O envio send_helpusai_simple_supervisor_test_20260616_009 chegou ao chat da HelpUSAI e ela respondeu "
            "RECEBIDO_HELPUSAI_SUPERVISOR_009 no chat destino."
        ),
        status="candidate",
        confidence=0.85,
        tags=("watcher", "ai_bridge_local", "interchat", "send_chat_message"),
    )


def recorder_status() -> dict[str, Any]:
    return {
        "enabled": operational_lessons_enabled(),
        "enabled_env": LESSON_MEMORY_ENABLED_ENV,
        "source": OPERATIONAL_LESSON_SOURCE,
        "project_id": OPERATIONAL_LESSON_PROJECT_ID,
        "automatic_rule_promotion": False,
        "requires_validation_before_promotion": True,
    }
