from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HelpUSOperationalContextCard:
    project: str = "HelpUSAI"
    assistant: str = "HelpUSAI"
    repo: str = "D:/dev/ai"
    environment: str = "Windows/PowerShell"
    current_micro: str = "Micro 13 - operational context card"
    previous_micro: str = "Micro 12 - readonly operator dashboard summary"

    def readonly_commands(self) -> list[str]:
        return [
            "git status -sb",
            "git status -s",
            "git log --oneline --decorate -8",
            "git diff --stat",
        ]

    def micro13_allowed_files(self) -> list[str]:
        return [
            "docs/HELPUS_OPERATIONAL_CONTEXT_CARD.md",
            "backend/helpus_operational_context_card.py",
            "scripts/watcher/smoke_helpus_operational_context_card.py",
            "docs/HELPUS_PROJECT_MASTER.md",
        ]

    def micro13_required_smokes(self) -> list[str]:
        return [
            "python -m py_compile backend/helpus_operational_context_card.py scripts/watcher/smoke_helpus_operational_context_card.py",
            "python scripts/watcher/smoke_helpus_operational_context_card.py",
            "python scripts/watcher/smoke_evolving_memory_operator_dashboard.py",
            "python scripts/watcher/smoke_docs_index.py",
            "git diff --check",
        ]

    def safety_restrictions(self) -> list[str]:
        return [
            "no deploy",
            "no external network",
            "no git reset",
            "no git clean",
            "no destructive deletion",
            "no automatic rule activation",
            "no public API exposure",
            "no unbounded recursive scan",
            "no huge inline command",
            "stop on failure",
        ]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["readonly_commands"] = self.readonly_commands()
        data["micro13_allowed_files"] = self.micro13_allowed_files()
        data["micro13_required_smokes"] = self.micro13_required_smokes()
        data["safety_restrictions"] = self.safety_restrictions()
        return data

    def compact_prompt(self) -> str:
        lines = [
            f"Assistant: {self.assistant}",
            f"Project: {self.project}",
            f"Repo: {self.repo}",
            f"Environment: {self.environment}",
            f"Current micro: {self.current_micro}",
            f"Previous micro: {self.previous_micro}",
            "Readonly first: " + "; ".join(self.readonly_commands()),
            "Allowed files: " + ", ".join(self.micro13_allowed_files()),
            "Required smokes: " + ", ".join(self.micro13_required_smokes()),
            "Safety: " + ", ".join(self.safety_restrictions()),
            "Rule: do not invent files, commands, smokes, or repo paths outside this card.",
        ]
        return "`n".join(lines)

    def validate_plan(self, repo: str, files: list[str], smokes: list[str]) -> dict[str, Any]:
        allowed_files = set(self.micro13_allowed_files())
        allowed_smokes = set(self.micro13_required_smokes())
        unknown_files = [item for item in files if item not in allowed_files]
        unknown_smokes = [item for item in smokes if item not in allowed_smokes]
        return {
            "repo_ok": repo == self.repo,
            "unknown_files": unknown_files,
            "unknown_smokes": unknown_smokes,
            "safe_to_continue": repo == self.repo and not unknown_files and not unknown_smokes,
        }


def build_helpus_operational_context_card() -> dict[str, Any]:
    return HelpUSOperationalContextCard().to_dict()


def build_helpus_operational_context_prompt() -> str:
    return HelpUSOperationalContextCard().compact_prompt()


def load_context_card_doc(path: str | Path = "docs/HELPUS_OPERATIONAL_CONTEXT_CARD.md") -> str:
    return Path(path).read_text(encoding="utf-8")
