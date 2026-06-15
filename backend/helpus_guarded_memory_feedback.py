from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass(frozen=True)
class HelpUSGuardedMemoryFeedback:
    event_type: str
    summary: str
    lessons_candidate: list[str] = field(default_factory=list)
    rules_candidate: list[str] = field(default_factory=list)
    can_promote_rules: bool = False
    requires_review: bool = True
    storage_mode: str = "draft_only"
    safety: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def build_guarded_memory_feedback(
    *,
    event_type: str,
    summary: str,
    lessons_candidate: list[str] | None = None,
    rules_candidate: list[str] | None = None,
    promote_rules: bool = False,
) -> dict[str, Any]:
    return HelpUSGuardedMemoryFeedback(
        event_type=event_type.strip(),
        summary=summary.strip(),
        lessons_candidate=lessons_candidate or [],
        rules_candidate=rules_candidate or [],
        can_promote_rules=False,
        requires_review=True,
        storage_mode="draft_only",
        safety={
            "writes_memory_automatically": False,
            "promotes_rules_automatically": False,
            "requires_human_review": True,
            "requested_promote_rules": bool(promote_rules),
        },
    ).to_dict()
