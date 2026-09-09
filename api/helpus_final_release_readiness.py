from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

HELPUSAI_FINAL_VERSION = "v0.29.0-dev"

REQUIRED_FINAL_SMOKES = [
    "python scripts/watcher/smoke_helpus_conversation_dry_run.py",
    "python scripts/watcher/smoke_helpus_command_envelope_export.py",
    "python scripts/watcher/smoke_helpus_readonly_execution_gate.py",
    "python scripts/watcher/smoke_helpus_patch_proposal_mode.py",
    "python scripts/watcher/smoke_helpus_human_approved_patch_apply.py",
    "python scripts/watcher/smoke_helpus_guarded_memory_feedback.py",
    "python scripts/watcher/smoke_helpus_final_release_readiness.py",
    "python scripts/watcher/smoke_helpus_runtime_feature_flags.py",
    "python scripts/watcher/smoke_helpus_chat_runtime_adapter.py",
    "python scripts/watcher/smoke_helpus_operator_visibility.py",
    "python scripts/watcher/smoke_helpus_chat_endpoint_wiring.py",
    "python scripts/watcher/smoke_helpus_conversation_api_adapter.py",
    "python scripts/watcher/smoke_helpus_conversation_response_composer.py",
    "python scripts/watcher/smoke_helpus_execution_envelope_builder.py",
    "python scripts/watcher/smoke_helpus_approval_gate.py",
    "python scripts/watcher/smoke_helpus_safe_command_planner.py",
    "python scripts/watcher/smoke_helpus_operational_context_card.py",
    "python scripts/watcher/smoke_evolving_memory_operator_dashboard.py",
    "python scripts/watcher/smoke_docs_index.py",
    "npm --prefix frontend run build",
    "git diff --check",
]

@dataclass(frozen=True)
class HelpUSFinalReleaseReadiness:
    version: str
    ready_for_release: bool
    required_smokes: list[str] = field(default_factory=list)
    safety_gates: list[str] = field(default_factory=list)
    remaining_manual_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def build_helpus_final_release_readiness() -> dict[str, Any]:
    return HelpUSFinalReleaseReadiness(
        version=HELPUSAI_FINAL_VERSION,
        ready_for_release=False,
        required_smokes=REQUIRED_FINAL_SMOKES,
        safety_gates=[
            "adapter disabled by default",
            "readonly execution gate does not execute automatically",
            "patch proposal mode does not apply patches",
            "human-approved patch apply model returns decision only",
            "memory feedback is draft_only and does not promote rules automatically",
        ],
        remaining_manual_steps=[
            "run final validation script",
            "review docs and badge strategy",
            "decide whether to remove temporary visual badge",
            "deploy only after explicit human approval",
        ],
    ).to_dict()
