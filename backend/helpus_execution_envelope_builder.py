from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_approval_gate import HelpUSApprovalGate
from backend.helpus_safe_command_planner import build_safe_command_plan


@dataclass(frozen=True)
class ReviewableExecutionEnvelope:
    intent: str
    action: str
    cwd: str
    timeout_seconds: int
    commands: list[str]
    decision: str
    risk_level: str
    allowed_files: list[str] = field(default_factory=list)
    validations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_allowed: bool = False
    requires_human_approval: bool = True
    stop_on_failure: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


class HelpUSExecutionEnvelopeBuilder:
    def __init__(self, gate: HelpUSApprovalGate | None = None) -> None:
        self.gate = gate or HelpUSApprovalGate()

    def build_from_intent(self, user_intent: str) -> ReviewableExecutionEnvelope:
        plan = build_safe_command_plan(user_intent)
        decision = self.gate.evaluate_plan(plan).to_dict()
        return self.build_from_plan_and_decision(plan, decision)

    def build_from_plan_and_decision(
        self,
        plan: dict[str, Any],
        decision: dict[str, Any],
    ) -> ReviewableExecutionEnvelope:
        plan_commands = list(plan.get("commands", []))
        allowed_commands = list(decision.get("allowed_commands", []))
        decision_name = str(decision.get("decision", "approval_required"))
        risk_level = str(decision.get("risk_level", plan.get("risk_level", "review")))
        cwd = str(plan.get("cwd", "D:/dev/ai"))
        timeout_seconds = int(plan.get("timeout_seconds", 120))
        allowed_files = list(decision.get("allowed_files", plan.get("allowed_files", [])))
        validations = list(plan.get("validations", []))

        warnings = [
            "Envelope is reviewable only; this builder does not execute commands.",
            "Use stop-on-failure and inspect stdout/stderr before continuing.",
        ]

        if decision_name == "blocked":
            warnings.extend(list(decision.get("reasons", [])))
            return ReviewableExecutionEnvelope(
                intent=str(plan.get("intent", "")),
                action="blocked",
                cwd=cwd,
                timeout_seconds=timeout_seconds,
                commands=[],
                decision=decision_name,
                risk_level=risk_level,
                allowed_files=[],
                validations=validations,
                warnings=warnings,
                execution_allowed=False,
                requires_human_approval=True,
                stop_on_failure=True,
            )

        if decision_name == "readonly_allowed":
            return ReviewableExecutionEnvelope(
                intent=str(plan.get("intent", "")),
                action="reviewable-run-command",
                cwd=cwd,
                timeout_seconds=timeout_seconds,
                commands=allowed_commands or plan_commands,
                decision=decision_name,
                risk_level=risk_level,
                allowed_files=[],
                validations=validations,
                warnings=warnings,
                execution_allowed=True,
                requires_human_approval=False,
                stop_on_failure=bool(decision.get("stop_on_failure", True)),
            )

        return ReviewableExecutionEnvelope(
            intent=str(plan.get("intent", "")),
            action="reviewable-approval-required",
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            commands=plan_commands,
            decision=decision_name,
            risk_level=risk_level,
            allowed_files=allowed_files,
            validations=validations,
            warnings=warnings + list(decision.get("reasons", [])),
            execution_allowed=False,
            requires_human_approval=True,
            stop_on_failure=bool(decision.get("stop_on_failure", True)),
        )


def build_reviewable_execution_envelope(user_intent: str) -> dict[str, Any]:
    return HelpUSExecutionEnvelopeBuilder().build_from_intent(user_intent).to_dict()


def build_reviewable_execution_envelope_json(user_intent: str) -> str:
    return HelpUSExecutionEnvelopeBuilder().build_from_intent(user_intent).to_json()
