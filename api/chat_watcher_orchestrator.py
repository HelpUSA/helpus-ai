from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.command_builder import CommandBuilder
from backend.operational_context import render_operational_summary
from backend.preflight_validator import PreflightValidator
from backend.watcher_intent import classify_watcher_intent
from backend.watcher_recovery import analyze_watcher_failure


@dataclass(frozen=True)
class ChatWatcherDecision:
    category: str
    action: str
    should_stop: bool
    summary: str
    envelope: dict[str, Any] | None
    recovery: dict[str, Any] | None


def _validate(envelope: dict[str, Any] | None) -> dict[str, Any] | None:
    if envelope is not None:
        PreflightValidator.validate(envelope)
    return envelope


def _build_run(
    source_chat_id: str,
    cwd: str,
    command: list[str],
    prefix: str,
    conversation_id: str,
    from_agent: str,
) -> dict[str, Any]:
    envelope = CommandBuilder.build_run_command(
        source_chat_id=source_chat_id,
        cwd=cwd,
        command=command,
        conversation_id=conversation_id,
        from_agent=from_agent,
        timeout_seconds=300,
    )
    envelope["command_id"] = prefix + "_" + envelope["command_id"]
    return _validate(envelope)


def _inspect_command() -> list[str]:
    return ["cmd", "/c", "git status -sb && git diff --stat && git diff --check"]


def _validate_command() -> list[str]:
    return [
        "cmd",
        "/c",
        "python scripts/watcher/smoke_operational_release.py && python scripts/watcher/smoke_health_report.py && npm --prefix frontend run build && git diff --check",
    ]


def orchestrate_chat_watcher(
    text: str,
    source_chat_id: str,
    cwd: str = "D:/dev/ai",
    conversation_id: str = "helpus_chat_watcher_orchestrator",
    from_agent: str = "HelpUS AI",
) -> dict[str, Any]:
    intent = classify_watcher_intent(text)
    context_summary = render_operational_summary().replace(chr(10), "; ")
    recovery = None
    envelope = None

    if intent["should_stop"]:
        action = "require_authorization"
        summary = "sensitive action blocked; explicit authorization required"
    elif intent["category"] == "result":
        action = "summarize_result"
        summary = "successful watcher receipt; summarize and continue"
    elif intent["category"] == "recover":
        action = "inspect_recovery"
        recovery = analyze_watcher_failure(text)
        summary = "failure receipt; inspect status and diff before fixing"
        envelope = _build_run(source_chat_id, cwd, _inspect_command(), "recover", conversation_id, from_agent)
    elif intent["category"] == "validate":
        action = "validate_suite"
        summary = "validation requested; run operational suite, health report, build, and diff-check"
        envelope = _build_run(source_chat_id, cwd, _validate_command(), "validate", conversation_id, from_agent)
    elif intent["category"] in {"commit", "tag"}:
        action = "inspect_before_change"
        summary = "change-control request; inspect status before commit or tag"
        envelope = _build_run(source_chat_id, cwd, _inspect_command(), "inspect", conversation_id, from_agent)
    else:
        action = "inspect"
        summary = "safe default inspection before proposing changes"
        envelope = _build_run(source_chat_id, cwd, _inspect_command(), "inspect", conversation_id, from_agent)

    decision = ChatWatcherDecision(
        category=intent["category"],
        action=action,
        should_stop=bool(intent["should_stop"]),
        summary=summary + "; " + context_summary,
        envelope=envelope,
        recovery=recovery,
    )
    return asdict(decision)


def build_status_message(decision: dict[str, Any]) -> str:
    return (
        "Status HelpUS AI: category {category} action {action} stop {stop} summary {summary}"
    ).format(
        category=decision["category"],
        action=decision["action"],
        stop=decision["should_stop"],
        summary=decision["summary"],
    )
