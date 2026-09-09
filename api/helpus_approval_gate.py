from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_safe_command_planner import SafeCommandPlan, build_safe_command_plan


@dataclass(frozen=True)
class ApprovalGateDecision:
    intent: str
    decision: str
    risk_level: str
    can_execute_readonly: bool
    requires_human_approval: bool
    is_blocked: bool
    reasons: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)
    allowed_files: list[str] = field(default_factory=list)
    stop_on_failure: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HelpUSApprovalGate:
    def evaluate_plan(self, plan: SafeCommandPlan | dict[str, Any]) -> ApprovalGateDecision:
        data = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)
        intent = str(data.get("intent", ""))
        risk_level = str(data.get("risk_level", "review"))
        commands = list(data.get("commands", []))
        allowed_files = list(data.get("allowed_files", []))
        blocked_reasons = list(data.get("blocked_reasons", []))
        requires_approval = bool(data.get("requires_human_approval", False))
        stop_on_failure = bool(data.get("stop_on_failure", True))

        if blocked_reasons or risk_level == "blocked":
            return ApprovalGateDecision(
                intent=intent,
                decision="blocked",
                risk_level=risk_level,
                can_execute_readonly=False,
                requires_human_approval=True,
                is_blocked=True,
                reasons=blocked_reasons or ["planner marked the command as blocked"],
                allowed_commands=[],
                allowed_files=[],
                stop_on_failure=True,
            )

        if risk_level == "low" and not allowed_files and not requires_approval:
            return ApprovalGateDecision(
                intent=intent,
                decision="readonly_allowed",
                risk_level=risk_level,
                can_execute_readonly=True,
                requires_human_approval=False,
                is_blocked=False,
                reasons=["low risk readonly plan", "no file changes requested"],
                allowed_commands=commands,
                allowed_files=[],
                stop_on_failure=stop_on_failure,
            )

        if risk_level in {"medium", "review"} or requires_approval or allowed_files:
            return ApprovalGateDecision(
                intent=intent,
                decision="approval_required",
                risk_level=risk_level,
                can_execute_readonly=False,
                requires_human_approval=True,
                is_blocked=False,
                reasons=["plan may change files or needs human review"],
                allowed_commands=commands,
                allowed_files=allowed_files,
                stop_on_failure=stop_on_failure,
            )

        return ApprovalGateDecision(
            intent=intent,
            decision="approval_required",
            risk_level=risk_level,
            can_execute_readonly=False,
            requires_human_approval=True,
            is_blocked=False,
            reasons=["unknown approval state"],
            allowed_commands=commands,
            allowed_files=allowed_files,
            stop_on_failure=stop_on_failure,
        )

    def evaluate_intent(self, user_intent: str) -> ApprovalGateDecision:
        return self.evaluate_plan(build_safe_command_plan(user_intent))


def evaluate_helpus_command_intent(user_intent: str) -> dict[str, Any]:
    return HelpUSApprovalGate().evaluate_intent(user_intent).to_dict()


def evaluate_helpus_command_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return HelpUSApprovalGate().evaluate_plan(plan).to_dict()
