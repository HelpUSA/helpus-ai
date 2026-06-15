from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_operational_context_card import HelpUSOperationalContextCard


DANGEROUS_TOKENS = (
    "git reset",
    "git clean",
    "rm -rf",
    "Remove-Item",
    "del /f",
    "format ",
    "shutdown",
    "sudo ",
    "curl ",
    "wget ",
    "Invoke-WebRequest",
    "iwr ",
    "Start-Process",
    "Set-ExecutionPolicy",
    "deploy",
)


@dataclass(frozen=True)
class SafeCommandPlan:
    intent: str
    cwd: str
    commands: list[str]
    timeout_seconds: int
    risk_level: str
    allowed_files: list[str] = field(default_factory=list)
    validations: list[str] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    stop_on_failure: bool = True
    requires_human_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def is_blocked(self) -> bool:
        return bool(self.blocked_reasons)


class HelpUSSafeCommandPlanner:
    def __init__(self, context: HelpUSOperationalContextCard | None = None) -> None:
        self.context = context or HelpUSOperationalContextCard()

    def plan(self, user_intent: str) -> SafeCommandPlan:
        intent = user_intent.strip()
        normalized = intent.lower()

        dangerous = self._dangerous_reasons(intent)
        if dangerous:
            return SafeCommandPlan(
                intent=intent,
                cwd=self.context.repo,
                commands=[],
                timeout_seconds=30,
                risk_level="blocked",
                allowed_files=[],
                validations=[],
                blocked_reasons=dangerous,
                requires_human_approval=True,
            )

        if self._looks_like_status_request(normalized):
            return SafeCommandPlan(
                intent=intent,
                cwd=self.context.repo,
                commands=self.context.readonly_commands(),
                timeout_seconds=120,
                risk_level="low",
                allowed_files=[],
                validations=["readonly only", "no file changes expected"],
            )

        if self._looks_like_smoke_request(normalized):
            return SafeCommandPlan(
                intent=intent,
                cwd=self.context.repo,
                commands=[
                    "python scripts/watcher/smoke_helpus_operational_context_card.py",
                    "python scripts/watcher/smoke_evolving_memory_operator_dashboard.py",
                    "python scripts/watcher/smoke_docs_index.py",
                    "git diff --check",
                ],
                timeout_seconds=300,
                risk_level="low",
                allowed_files=[],
                validations=["smokes only", "stop on first failure"],
            )

        if self._looks_like_micro14_patch_request(normalized):
            return SafeCommandPlan(
                intent=intent,
                cwd=self.context.repo,
                commands=[
                    "git status -sb",
                    "git status -s",
                    "python -m py_compile backend/helpus_safe_command_planner.py scripts/watcher/smoke_helpus_safe_command_planner.py",
                    "python scripts/watcher/smoke_helpus_safe_command_planner.py",
                    "python scripts/watcher/smoke_helpus_operational_context_card.py",
                    "python scripts/watcher/smoke_docs_index.py",
                    "git diff --check",
                ],
                timeout_seconds=420,
                risk_level="medium",
                allowed_files=[
                    "backend/helpus_safe_command_planner.py",
                    "scripts/watcher/smoke_helpus_safe_command_planner.py",
                    "docs/HELPUS_PROJECT_MASTER.md",
                ],
                validations=["allowlist required", "py_compile required", "smoke required", "docs smoke required"],
                requires_human_approval=True,
            )

        return SafeCommandPlan(
            intent=intent,
            cwd=self.context.repo,
            commands=self.context.readonly_commands(),
            timeout_seconds=120,
            risk_level="review",
            allowed_files=[],
            validations=["unknown intent; inspect first", "ask for context if needed"],
            requires_human_approval=True,
        )

    def _dangerous_reasons(self, text: str) -> list[str]:
        found: list[str] = []
        lower = text.lower()
        for token in DANGEROUS_TOKENS:
            if token.lower() in lower:
                found.append(f"blocked dangerous token: {token}")
        return found

    def _looks_like_status_request(self, normalized: str) -> bool:
        keywords = ("status", "estado", "inspect", "inspec", "verifique", "diagnostico", "readonly")
        return any(keyword in normalized for keyword in keywords)

    def _looks_like_smoke_request(self, normalized: str) -> bool:
        keywords = ("smoke", "validar", "validation", "teste", "tests")
        return any(keyword in normalized for keyword in keywords)

    def _looks_like_micro14_patch_request(self, normalized: str) -> bool:
        return ("micro 14" in normalized or "safe command planner" in normalized or "command planner" in normalized)


def build_safe_command_plan(user_intent: str) -> dict[str, Any]:
    return HelpUSSafeCommandPlanner().plan(user_intent).to_dict()
