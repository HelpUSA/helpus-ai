from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass(frozen=True)
class HelpUSHumanApprovedPatchApplyDecision:
    approved: bool
    can_apply: bool
    reason: str
    allowed_files: list[str] = field(default_factory=list)
    blocked_files: list[str] = field(default_factory=list)
    required_validations: list[str] = field(default_factory=list)
    applies_now: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def evaluate_human_approved_patch_apply(
    *,
    explicit_approval: bool,
    requested_files: list[str],
    allowed_files: list[str],
    required_validations: list[str] | None = None,
) -> dict[str, Any]:
    validations = required_validations or [
        "py_compile affected python files",
        "run affected smoke scripts",
        "git diff --check",
    ]
    allowed_set = set(allowed_files)
    blocked = [path for path in requested_files if path not in allowed_set]

    if not explicit_approval:
        return HelpUSHumanApprovedPatchApplyDecision(
            approved=False,
            can_apply=False,
            reason="explicit human approval missing",
            allowed_files=allowed_files,
            blocked_files=blocked,
            required_validations=validations,
            applies_now=False,
        ).to_dict()

    if blocked:
        return HelpUSHumanApprovedPatchApplyDecision(
            approved=True,
            can_apply=False,
            reason="requested files outside allowlist",
            allowed_files=allowed_files,
            blocked_files=blocked,
            required_validations=validations,
            applies_now=False,
        ).to_dict()

    return HelpUSHumanApprovedPatchApplyDecision(
        approved=True,
        can_apply=True,
        reason="human approved and files are inside allowlist",
        allowed_files=allowed_files,
        blocked_files=[],
        required_validations=validations,
        applies_now=False,
    ).to_dict()
