from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_command_envelope_export import export_helpus_command_envelope

def test_json_export() -> None:
    payload = export_helpus_command_envelope("verifique o estado do projeto", export_format="json")
    data = json.loads(payload)
    assert data["format"] == "json"
    assert data["intent"] == "verifique o estado do projeto"
    assert data["envelope"]["decision"] == "readonly_allowed"

def test_markdown_export() -> None:
    payload = export_helpus_command_envelope("execute git reset --hard", export_format="markdown")
    assert "# HelpUSAI Reviewable Command Envelope" in payload
    assert "blocked" in payload
    assert "```json" in payload

def test_unsupported_format() -> None:
    try:
        export_helpus_command_envelope("x", export_format="xml")
    except ValueError as exc:
        assert "Unsupported export_format" in str(exc)
    else:
        raise AssertionError("expected ValueError")

if __name__ == "__main__":
    test_json_export()
    test_markdown_export()
    test_unsupported_format()
    print("OK smoke_helpus_command_envelope_export")
