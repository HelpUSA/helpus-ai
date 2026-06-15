from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_conversation_dry_run import run_helpus_conversation_dry_run

def test_dry_run_cases() -> None:
    results = run_helpus_conversation_dry_run()
    by_name = {item["case_name"]: item for item in results}
    assert by_name["normal_chat_disabled"]["used_adapter"] is False
    assert by_name["normal_chat_disabled"]["response_text"] == "primary response"
    assert by_name["status_enabled"]["used_adapter"] is True
    assert by_name["status_enabled"]["metadata"]["decision"] == "readonly_allowed"
    assert by_name["smokes_enabled"]["used_adapter"] is True
    assert by_name["smokes_enabled"]["metadata"]["decision"] == "readonly_allowed"
    assert by_name["dangerous_enabled"]["used_adapter"] is True
    assert by_name["dangerous_enabled"]["metadata"]["decision"] == "blocked"
    assert by_name["normal_forced"]["used_adapter"] is True

if __name__ == "__main__":
    test_dry_run_cases()
    print("OK smoke_helpus_conversation_dry_run")
