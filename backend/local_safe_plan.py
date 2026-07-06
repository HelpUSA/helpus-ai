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


# PHASE_B_CUSTOM_PLAN_CONTRACT_OVERRIDE
PLAN_CONTRACT_VERSION = "local-plan-v1"
MAX_COMMANDS = 5
MAX_COMMAND_LENGTH = 240
PHASE_B_INTENTS = {
    "phase_a_validation": ["npm run smoke:phase-a"],
    "phase_b_validation": ["npm run smoke:phase-b"],
    "local_status": ["git status -sb"],
    "local_diff": ["git diff --stat", "git diff --check"],
    "local_recent_commits": ["git log --oneline --decorate -8"],
    "local_api_smoke": ["npm run smoke:local-api"],
    "admin_local_smoke": ["npm run smoke:admin-local"],
    "build": ["npm run build"],
}
PHASE_B_DESC = {
    "phase_a_validation": "Valida a Fase A completa.",
    "phase_b_validation": "Valida a Fase B plan-only.",
    "local_status": "Consulta status Git local.",
    "local_diff": "Consulta diff local sem modificar arquivos.",
    "local_recent_commits": "Consulta commits recentes.",
    "local_api_smoke": "Executa smoke da API local.",
    "admin_local_smoke": "Executa smokes do admin local.",
    "build": "Executa build de produção.",
}
PHASE_B_ALLOW = (
    "git status", "git diff --stat", "git diff --check", "git diff --name-only", "git log --oneline",
    "npm run smoke:phase-a", "npm run smoke:phase-b", "npm run smoke:phase-b-plan", "npm run smoke:phase-b-ui",
    "npm run smoke:local-api", "npm run smoke:admin-local", "npm run build",
    "python scripts/34_smoke_local_readonly_api.py", "python scripts/35_smoke_local_safe_plan.py",
    "python scripts/36_smoke_local_plan_contract.py", "python scripts/helpusai/smoke_admin_local_readonly_panel.py",
    "python scripts/helpusai/smoke_admin_local_readonly_link.py", "python scripts/helpusai/smoke_admin_local_safe_plan_panel.py",
    "python scripts/helpusai/smoke_admin_local_custom_plan_panel.py", "python -m py_compile",
)
PHASE_B_BLOCK = ("git push", "git commit", "git add", "git reset", "git clean", "rm ", "remove-item", "del ", "erase ", "rmdir", "curl", "wget", "invoke-webrequest", "invoke-restmethod", "deploy", "vercel", "railway", "npm publish", "pip install", "ssh ", "scp ")
PHASE_B_SEP = ("&&", "||", ";", "`", "$(", ">", "<")

def list_local_plan_intents():
    return {"ok": True, "mode": "plan_only", "version": PLAN_CONTRACT_VERSION, "executed": False, "intents": [{"intent": k, "description": PHASE_B_DESC.get(k, "Intent read-only."), "commands": v} for k, v in PHASE_B_INTENTS.items()]}

def _phase_b_norm(x):
    if isinstance(x, str): return " ".join(x.strip().split())
    if isinstance(x, list): return " ".join(str(i).strip() for i in x if str(i).strip())
    return ""

def _phase_b_result(ok, allowed, risk, reason, intent, commands, blocked_reasons, summary):
    return {"ok": ok, "mode": "plan_only", "version": PLAN_CONTRACT_VERSION, "executed": False, "allowed": allowed, "risk": risk, "reason": reason, "intent": intent, "commands": commands, "blocked_reasons": blocked_reasons, "requires_human_confirmation": True, "summary": summary}

def plan_local_action(payload):
    payload = payload or {}
    intent = str(payload.get("intent") or "custom").strip() or "custom"
    if intent in PHASE_B_INTENTS:
        commands = PHASE_B_INTENTS[intent]
    elif isinstance(payload.get("commands"), list):
        commands = [c for c in (_phase_b_norm(c) for c in payload.get("commands")) if c]
    else:
        c = _phase_b_norm(payload.get("command"))
        commands = [c] if c else []
    if not commands:
        return _phase_b_result(False, False, "unknown", "no_command_or_known_intent", intent, [], [], "Nenhuma intent conhecida ou comando foi informado para planejamento.")
    if len(commands) > MAX_COMMANDS:
        return _phase_b_result(True, False, "blocked", "too_many_commands", intent, commands[:MAX_COMMANDS], [f"too_many_commands:max_{MAX_COMMANDS}"], "O plano excede o limite de comandos permitido pelo contrato plan-only.")
    blocked=[]; review=[]
    for cmd in commands:
        low=cmd.lower()
        if len(cmd)>MAX_COMMAND_LENGTH: blocked.append(f"command_too_long:max_{MAX_COMMAND_LENGTH}")
        blocked += [f"blocked_token:{t.strip()}" for t in PHASE_B_BLOCK if t in low]
        blocked += [f"blocked_separator:{sep}" for sep in PHASE_B_SEP if sep in cmd]
        if not any(low.startswith(a.lower()) for a in PHASE_B_ALLOW): review.append(cmd)
    if blocked:
        return _phase_b_result(True, False, "blocked", "blocked_command_detected", intent, commands, sorted(set(blocked)), "O planner detectou comando, token ou separador bloqueado. Nada foi executado.")
    if review:
        return _phase_b_result(True, False, "needs_review", "command_not_in_readonly_allowlist", intent, commands, [f"not_allowlisted:{x}" for x in review], "O comando nao esta na allowlist read-only e precisa de revisao humana.")
    return _phase_b_result(True, True, "readonly", "readonly_plan_allowed_but_not_executed", intent, commands, [], "Plano read-only permitido para planejamento. Nenhum comando foi executado.")
