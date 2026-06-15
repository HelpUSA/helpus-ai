from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from backend.helpus_execution_envelope_builder import build_reviewable_execution_envelope

@dataclass(frozen=True)
class HelpUSCommandEnvelopeExport:
    format: str
    intent: str
    review_required: bool
    envelope: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        envelope_json = json.dumps(self.envelope, ensure_ascii=False, indent=2, sort_keys=True)
        lines = [
            "# HelpUSAI Reviewable Command Envelope",
            "",
            f"- Intent: {self.intent}",
            f"- Review required: {'yes' if self.review_required else 'no'}",
            "",
            "## Warnings",
            "",
        ]
        lines.extend(f"- {warning}" for warning in (self.warnings or ["Review before execution."]))
        lines.extend(["", "## Envelope JSON", "", "```json", envelope_json, "```"])
        return "\n".join(lines)

def export_helpus_command_envelope(user_intent: str, *, export_format: str = "json") -> str:
    envelope = build_reviewable_execution_envelope(user_intent)
    payload = HelpUSCommandEnvelopeExport(
        format=export_format,
        intent=user_intent.strip(),
        review_required=bool(envelope.get("requires_human_approval", True)),
        envelope=envelope,
        warnings=list(envelope.get("warnings", [])),
    )
    if export_format == "json":
        return payload.to_json()
    if export_format == "markdown":
        return payload.to_markdown()
    raise ValueError(f"Unsupported export_format: {export_format}")
