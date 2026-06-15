from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_approval_gate import HelpUSApprovalGate
from backend.helpus_execution_envelope_builder import HelpUSExecutionEnvelopeBuilder
from backend.helpus_operational_context_card import HelpUSOperationalContextCard
from backend.helpus_safe_command_planner import build_safe_command_plan


@dataclass(frozen=True)
class HelpUSConversationResponse:
    message: str
    intent: str
    repo: str
    risk_level: str
    decision: str
    action: str
    commands: list[str] = field(default_factory=list)
    allowed_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_step: str = ""
    requires_human_approval: bool = True
    execution_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HelpUSConversationResponseComposer:
    def __init__(
        self,
        context: HelpUSOperationalContextCard | None = None,
        gate: HelpUSApprovalGate | None = None,
        envelope_builder: HelpUSExecutionEnvelopeBuilder | None = None,
    ) -> None:
        self.context = context or HelpUSOperationalContextCard()
        self.gate = gate or HelpUSApprovalGate()
        self.envelope_builder = envelope_builder or HelpUSExecutionEnvelopeBuilder(self.gate)

    def compose(self, user_intent: str) -> HelpUSConversationResponse:
        plan = build_safe_command_plan(user_intent)
        decision = self.gate.evaluate_plan(plan).to_dict()
        envelope = self.envelope_builder.build_from_plan_and_decision(plan, decision).to_dict()

        decision_name = str(envelope.get("decision", "approval_required"))
        action = str(envelope.get("action", "reviewable-approval-required"))
        risk_level = str(envelope.get("risk_level", "review"))
        commands = list(envelope.get("commands", []))
        allowed_files = list(envelope.get("allowed_files", []))
        warnings = list(envelope.get("warnings", []))
        requires_approval = bool(envelope.get("requires_human_approval", True))
        execution_allowed = bool(envelope.get("execution_allowed", False))

        message = self._build_message(
            intent=user_intent,
            decision=decision_name,
            action=action,
            risk_level=risk_level,
            commands=commands,
            allowed_files=allowed_files,
            warnings=warnings,
            requires_approval=requires_approval,
            execution_allowed=execution_allowed,
        )

        return HelpUSConversationResponse(
            message=message,
            intent=user_intent.strip(),
            repo=self.context.repo,
            risk_level=risk_level,
            decision=decision_name,
            action=action,
            commands=commands,
            allowed_files=allowed_files,
            warnings=warnings,
            next_step=self._next_step(decision_name, execution_allowed, requires_approval),
            requires_human_approval=requires_approval,
            execution_allowed=execution_allowed,
        )

    def _build_message(
        self,
        *,
        intent: str,
        decision: str,
        action: str,
        risk_level: str,
        commands: list[str],
        allowed_files: list[str],
        warnings: list[str],
        requires_approval: bool,
        execution_allowed: bool,
    ) -> str:
        lines = [
            f"Repo: {self.context.repo}",
            f"Ambiente: {self.context.environment}",
            f"Intencao: {intent.strip()}",
            f"Risco: {risk_level}",
            f"Decisao: {decision}",
            f"Acao: {action}",
        ]

        if commands:
            lines.append("Comandos sugeridos:")
            lines.extend(f"- {command}" for command in commands)
        else:
            lines.append("Comandos sugeridos: nenhum")

        if allowed_files:
            lines.append("Arquivos permitidos:")
            lines.extend(f"- {file}" for file in allowed_files)

        if warnings:
            lines.append("Avisos:")
            lines.extend(f"- {warning}" for warning in warnings[:3])

        approval_text = "sim" if requires_approval else "nao"
        execution_text = "sim" if execution_allowed else "nao"
        lines.append(f"Aprovacao humana: {approval_text}")
        lines.append(f"Execucao permitida pelo gate: {execution_text}")
        lines.append("Regra: parar em qualquer falha e reportar stdout/stderr.")
        lines.append("Proximo passo: " + self._next_step(decision, execution_allowed, requires_approval))
        return "`n".join(lines)

    def _next_step(self, decision: str, execution_allowed: bool, requires_approval: bool) -> str:
        if decision == "blocked":
            return "nao executar; revisar motivo do bloqueio"
        if execution_allowed and not requires_approval:
            return "revisar comandos readonly e executar somente se o usuario autorizar"
        return "pedir aprovacao humana antes de qualquer patch ou execucao"


def compose_helpus_response(user_intent: str) -> dict[str, Any]:
    return HelpUSConversationResponseComposer().compose(user_intent).to_dict()


def compose_helpus_message(user_intent: str) -> str:
    return HelpUSConversationResponseComposer().compose(user_intent).message
