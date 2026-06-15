from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.helpus_guarded_memory_feedback import build_guarded_memory_feedback

def test_memory_feedback_draft_only() -> None:
    feedback = build_guarded_memory_feedback(
        event_type="smoke_result",
        summary="all smokes passed",
        lessons_candidate=["keep batches guarded"],
        rules_candidate=["never auto promote"],
        promote_rules=True,
    )
    assert feedback["storage_mode"] == "draft_only"
    assert feedback["can_promote_rules"] is False
    assert feedback["requires_review"] is True
    assert feedback["safety"]["writes_memory_automatically"] is False
    assert feedback["safety"]["promotes_rules_automatically"] is False
    assert feedback["safety"]["requested_promote_rules"] is True

if __name__ == "__main__":
    test_memory_feedback_draft_only()
    print("OK smoke_helpus_guarded_memory_feedback")
