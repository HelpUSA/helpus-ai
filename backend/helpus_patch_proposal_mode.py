from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_readonly_execution_gate import evaluate_readonly_execution_gate

@dataclass(frozen=True)
class HelpUSPatchProposal:
    intent: str
    mode: str
    allowed_files: list[str] = field(default_factory=list)
    proposed_steps: list[str] = field(default_factory=list)
    required_validations: list[str] = field(default_factory=list)
    risk_level: str = "review"
    can_apply_automatically: bool = False
    requires_human_approval: bool = True
    reason: str = "patch proposal only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

DEFAULT_PATCH_VALIDATIONS = [
    "git status -sb",
    "git status -s",
    "python -m py_compile changed python files",
    "run affected smoke scripts",
    "python scripts/watcher/smoke_docs_index.py when docs change",
    "npm --prefix frontend run build when frontend changes",
    "git diff --check",
]

def build_helpus_patch_proposal(
    intent: str,
    *,
    allowed_files: list[str] | None = None,
    proposed_steps: list[str] | None = None,
    required_validations: list[str] | None = None,
) -> dict[str, Any]:
    readonly_decision = evaluate_readonly_execution_gate(intent)
    files = allowed_files or []
    steps = proposed_steps or [
        "inspect current repo state",
        "prepare minimal diff proposal",
        "show touched files before apply",
        "wait for explicit human approval",
    ]
    validations = required_validations or DEFAULT_PATCH_VALIDATIONS

    risk = "medium" if files else "review"
    if readonly_decision.get("allowed") is True:
        risk = "low"

    return HelpUSPatchProposal(
        intent=intent.strip(),
        mode="proposal_only",
        allowed_files=files,
        proposed_steps=steps,
        required_validations=validations,
        risk_level=risk,
        can_apply_automatically=False,
        requires_human_approval=True,
        reason="patch proposal is reviewable only; no filesystem mutation is performed by this module",
    ).to_dict()
