from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_execution_envelope_builder import build_reviewable_execution_envelope

READONLY_PREFIXES = (
    "git status",
    "git log",
    "git diff --stat",
    "git diff --name-only",
    "git diff --check",
    "python scripts/watcher/smoke_",
    "python -m py_compile",
)

BLOCKED_TOKENS = (
    "git push",
    "git commit",
    "git add",
    "git reset",
    "git clean",
    "rm ",
    "remove-item",
    "del ",
    "curl",
    "wget",
    "invoke-webrequest",
    "deploy",
)

@dataclass(frozen=True)
class HelpUSReadonlyExecutionGateDecision:
    intent: str
    allowed: bool
    reason: str
    commands: list[str] = field(default_factory=list)
    blocked_commands: list[str] = field(default_factory=list)
    cwd: str = "D:/dev/ai"
    timeout_seconds: int = 120
    executes_now: bool = False
    source_decision: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _is_readonly_command(command: str) -> bool:
    normalized = command.strip().lower()
    if any(token in normalized for token in BLOCKED_TOKENS):
        return False
    return any(normalized.startswith(prefix) for prefix in READONLY_PREFIXES)

def evaluate_readonly_execution_gate(user_intent: str) -> dict[str, Any]:
    envelope = build_reviewable_execution_envelope(user_intent)
    commands = list(envelope.get("commands", []))
    decision = str(envelope.get("decision", "approval_required"))
    action = str(envelope.get("action", "reviewable-approval-required"))
    timeout_seconds = int(envelope.get("timeout_seconds", 120))

    if decision == "blocked" or action == "blocked":
        return HelpUSReadonlyExecutionGateDecision(
            intent=user_intent.strip(),
            allowed=False,
            reason="blocked envelope",
            commands=[],
            blocked_commands=commands,
            timeout_seconds=timeout_seconds,
            source_decision=decision,
        ).to_dict()

    if decision != "readonly_allowed":
        return HelpUSReadonlyExecutionGateDecision(
            intent=user_intent.strip(),
            allowed=False,
            reason="approval required before readonly execution",
            commands=[],
            blocked_commands=commands,
            timeout_seconds=timeout_seconds,
            source_decision=decision,
        ).to_dict()

    blocked = [command for command in commands if not _is_readonly_command(command)]
    allowed_commands = [command for command in commands if _is_readonly_command(command)]

    if blocked:
        return HelpUSReadonlyExecutionGateDecision(
            intent=user_intent.strip(),
            allowed=False,
            reason="non-readonly commands present",
            commands=allowed_commands,
            blocked_commands=blocked,
            timeout_seconds=timeout_seconds,
            source_decision=decision,
        ).to_dict()

    if not allowed_commands:
        return HelpUSReadonlyExecutionGateDecision(
            intent=user_intent.strip(),
            allowed=False,
            reason="no readonly commands available",
            commands=[],
            blocked_commands=[],
            timeout_seconds=timeout_seconds,
            source_decision=decision,
        ).to_dict()

    return HelpUSReadonlyExecutionGateDecision(
        intent=user_intent.strip(),
        allowed=True,
        reason="readonly commands allowed for manual execution",
        commands=allowed_commands,
        blocked_commands=[],
        timeout_seconds=timeout_seconds,
        executes_now=False,
        source_decision=decision,
    ).to_dict()
