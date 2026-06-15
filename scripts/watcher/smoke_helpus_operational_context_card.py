from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_operational_context_card import (
    HelpUSOperationalContextCard,
    build_helpus_operational_context_card,
    build_helpus_operational_context_prompt,
    load_context_card_doc,
)


def test_context_card() -> None:
    card = HelpUSOperationalContextCard()
    data = build_helpus_operational_context_card()
    prompt = build_helpus_operational_context_prompt()
    doc = load_context_card_doc(ROOT / "docs" / "HELPUS_OPERATIONAL_CONTEXT_CARD.md")

    assert data["assistant"] == "HelpUSAI"
    assert data["project"] == "HelpUSAI"
    assert data["repo"] == "D:/dev/ai"
    assert data["environment"] == "Windows/PowerShell"
    assert "Micro 13" in data["current_micro"]

    assert "git status -sb" in data["readonly_commands"]
    assert "git status -s" in data["readonly_commands"]
    assert "git log --oneline --decorate -8" in data["readonly_commands"]
    assert "git diff --stat" in data["readonly_commands"]

    assert "docs/HELPUS_OPERATIONAL_CONTEXT_CARD.md" in data["micro13_allowed_files"]
    assert "backend/helpus_operational_context_card.py" in data["micro13_allowed_files"]
    assert "scripts/watcher/smoke_helpus_operational_context_card.py" in data["micro13_allowed_files"]
    assert "docs/HELPUS_PROJECT_MASTER.md" in data["micro13_allowed_files"]

    assert "python scripts/watcher/smoke_helpus_operational_context_card.py" in data["micro13_required_smokes"]
    assert "python scripts/watcher/smoke_evolving_memory_operator_dashboard.py" in data["micro13_required_smokes"]
    assert "python scripts/watcher/smoke_docs_index.py" in data["micro13_required_smokes"]
    assert "git diff --check" in data["micro13_required_smokes"]

    safety = " ".join(data["safety_restrictions"])
    for item in ["no deploy", "no external network", "no git reset", "no git clean", "no automatic rule activation"]:
        assert item in safety

    assert "do not invent" in prompt.lower()
    assert "D:/dev/ai" in prompt
    assert "HelpUSAI Operational Context Card" in doc
    assert "Micro 13" in doc

    ok = card.validate_plan(
        repo="D:/dev/ai",
        files=[
            "docs/HELPUS_OPERATIONAL_CONTEXT_CARD.md",
            "backend/helpus_operational_context_card.py",
            "scripts/watcher/smoke_helpus_operational_context_card.py",
            "docs/HELPUS_PROJECT_MASTER.md",
        ],
        smokes=[
            "python scripts/watcher/smoke_helpus_operational_context_card.py",
            "python scripts/watcher/smoke_evolving_memory_operator_dashboard.py",
            "python scripts/watcher/smoke_docs_index.py",
            "git diff --check",
        ],
    )
    assert ok["safe_to_continue"] is True

    bad = card.validate_plan(repo="D:/wrong", files=["x.py"], smokes=["python bad.py"])
    assert bad["safe_to_continue"] is False
    assert bad["unknown_files"] == ["x.py"]
    assert bad["unknown_smokes"] == ["python bad.py"]

    source = (ROOT / "backend" / "helpus_operational_context_card.py").read_text(encoding="utf-8")
    for forbidden in ["subprocess", "requests", "urllib", "http.client", "socket"]:
        assert forbidden not in source


if __name__ == "__main__":
    test_context_card()
    print("OK smoke_helpus_operational_context_card")
