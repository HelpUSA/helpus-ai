from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LocalPlanResult:
    ok: bool
    mode: str
    executed: bool
    allowed: bool
    risk: str
    reason: str
    intent: str
    commands: list[str]
    blocked_reasons: list[str]
    requires_human_confirmation: bool


READONLY_INTENT_COMMANDS: dict[str, list[str]] = {
    "phase_a_validation": ["npm run smoke:phase-a"],
    "local_status": ["git status -sb"],
    "local_diff": ["git diff --stat", "git diff --check"],
    "local_api_smoke": ["npm run smoke:local-api"],
    "admin_local_smoke": ["npm run smoke:admin-local"],
    "build": ["npm run build"],
}

ALLOWLIST_PREFIXES = (
    "git status",
    "git diff --stat",
    "git diff --check",
    "git diff --name-only",
    "git log --oneline",
    "npm run smoke:phase-a",
    "npm run smoke:local-api",
    "npm run smoke:admin-local",
    "npm run build",
    "python scripts/34_smoke_local_readonly_api.py",
    "python scripts/helpusai/smoke_admin_local_readonly_panel.py",
    "python scripts/helpusai/smoke_admin_local_readonly_link.py",
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
    "erase ",
    "rmdir",
    "curl",
    "wget",
    "invoke-webrequest",
    "deploy",
    "vercel",
    "railway",
    "npm publish",
    "pip install",
    "ssh ",
    "scp ",
)


def _normalize_command(command: Any) -> str:
    if isinstance(command, str):
        return " ".join(command.strip().split())
    if isinstance(command, list):
        return " ".join(str(part).strip() for part in command if str(part).strip())
    return ""


def _blocked_reasons(command: str) -> list[str]:
    lower = command.lower()
    return [f"blocked_token:{token.strip()}" for token in BLOCKED_TOKENS if token in lower]


def _is_allowlisted(command: str) -> bool:
    lower = command.lower()
    return any(lower.startswith(prefix.lower()) for prefix in ALLOWLIST_PREFIXES)


def _commands_from_payload(payload: dict[str, Any], intent: str) -> list[str]:
    if intent in READONLY_INTENT_COMMANDS:
        return READONLY_INTENT_COMMANDS[intent]
    raw_commands = payload.get("commands")
    if isinstance(raw_commands, list):
        commands = [_normalize_command(command) for command in raw_commands]
        return [command for command in commands if command]
    command = _normalize_command(payload.get("command"))
    return [command] if command else []


def plan_local_action(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Return a safe plan only. This function never executes commands."""
    payload = payload or {}
    intent = str(payload.get("intent") or "custom").strip() or "custom"
    commands = _commands_from_payload(payload, intent)

    if not commands:
        return asdict(
            LocalPlanResult(
                ok=False,
                mode="plan_only",
                executed=False,
                allowed=False,
                risk="unknown",
                reason="no_command_or_known_intent",
                intent=intent,
                commands=[],
                blocked_reasons=[],
                requires_human_confirmation=True,
            )
        )

    blocked: list[str] = []
    not_allowlisted: list[str] = []
    for command in commands:
        blocked.extend(_blocked_reasons(command))
        if not _is_allowlisted(command):
            not_allowlisted.append(command)

    if blocked:
        return asdict(
            LocalPlanResult(
                ok=True,
                mode="plan_only",
                executed=False,
                allowed=False,
                risk="blocked",
                reason="blocked_command_detected",
                intent=intent,
                commands=commands,
                blocked_reasons=sorted(set(blocked)),
                requires_human_confirmation=True,
            )
        )

    if not_allowlisted:
        return asdict(
            LocalPlanResult(
                ok=True,
                mode="plan_only",
                executed=False,
                allowed=False,
                risk="needs_review",
                reason="command_not_in_readonly_allowlist",
                intent=intent,
                commands=commands,
                blocked_reasons=[f"not_allowlisted:{command}" for command in not_allowlisted],
                requires_human_confirmation=True,
            )
        )

    return asdict(
        LocalPlanResult(
            ok=True,
            mode="plan_only",
            executed=False,
            allowed=True,
            risk="readonly",
            reason="readonly_plan_allowed_but_not_executed",
            intent=intent,
            commands=commands,
            blocked_reasons=[],
            requires_human_confirmation=True,
        )
    )
