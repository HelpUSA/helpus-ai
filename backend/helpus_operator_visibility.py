from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from backend.helpus_runtime_feature_flags import load_helpus_runtime_feature_flags

HELPUSAI_VISUAL_VERSION = "v0.22.0-dev"

MICRO_CHAIN = [
    "Micro 12 - readonly operator dashboard",
    "Micro 13 - operational context card",
    "Micro 14 - safe command planner",
    "Micro 15 - approval gate",
    "Micro 16 - execution envelope builder",
    "Micro 17 - conversation response composer",
    "Micro 18 - conversation API adapter",
    "Micro 19 - chat endpoint wiring guard",
    "Micro 20 - runtime feature flags",
    "Micro 21 - guarded runtime adapter smoke",
    "Micro 22 - operator visibility status",
]

@dataclass(frozen=True)
class HelpUSOperatorVisibility:
    version: str
    latest_micro: str
    feature_flags: dict[str, Any]
    chain: list[str] = field(default_factory=list)
    safety: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def build_helpus_operator_visibility(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    flags = load_helpus_runtime_feature_flags(env).to_dict()
    return HelpUSOperatorVisibility(
        version=HELPUSAI_VISUAL_VERSION,
        latest_micro="Micro 22 - operator visibility status",
        feature_flags=flags,
        chain=MICRO_CHAIN,
        safety={
            "executes_commands": False,
            "changes_files": False,
            "calls_network": False,
            "adapter_default_enabled": False,
            "human_review_required_before_execution": True,
        },
    ).to_dict()
