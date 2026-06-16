from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "page.tsx"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    text = PAGE.read_text(encoding="utf-8")

    check("type AgentTraceItem = {" in text, "missing AgentTraceItem type")
    check("agent_trace?: AgentTraceItem[]" in text, "missing message agent_trace type")
    check("const defaultAgentTrace: AgentTraceItem[] = [" in text, "missing default trace")
    check("activeAgentTrace" in text, "missing active trace state")
    check("setActiveAgentTrace(defaultAgentTrace)" in text, "missing initial visible trace")
    check("Array.isArray(data.agent_trace)" in text, "missing backend trace parsing")
    check("agent_trace: responseAgentTrace" in text, "missing trace mapping to assistant message")
    check("window.setTimeout(() => setActiveAgentTrace([]), 2600)" in text, "missing trace auto-collapse")
    check("Trabalho interno da HelpUSAI" in text, "missing visible trace UI")
    check("step.status === 'done'" in text, "missing status styling")
    check("chain-of-thought" not in text.lower(), "frontend must not expose chain-of-thought wording")

    print("OK smoke_frontend_agent_trace")


if __name__ == "__main__":
    main()
