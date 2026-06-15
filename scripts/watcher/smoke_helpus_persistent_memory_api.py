from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import tempfile

from backend.helpus_persistent_memory_api import (
    create_feedback_draft_payload,
    memory_status_payload,
    recent_memory_payload,
)
from backend.helpus_persistent_memory_store import PersistentMemoryStore

with tempfile.TemporaryDirectory() as tmp:
    store = PersistentMemoryStore(Path(tmp) / "api-memory.db")

    status = memory_status_payload(store)
    if status["event_count"] != 0:
        raise SystemExit("expected empty API status")

    event_id = store.record_event(
        event_type="api_smoke",
        source="smoke",
        summary="API smoke event",
        details={"api": True},
    )

    recent = recent_memory_payload(store, limit=5)
    if recent["readonly"] is not True:
        raise SystemExit("recent payload must be readonly")
    if recent["items"][0]["id"] != event_id:
        raise SystemExit("recent payload missing event")

    feedback = create_feedback_draft_payload(
        event_id=event_id,
        feedback_type="api_feedback",
        source="smoke",
        summary="API feedback draft",
        details={"draft": True},
        store=store,
    )

    if feedback["status"] != "draft":
        raise SystemExit("feedback API must create draft")
    if feedback["automatic_rule_promotion"] is not False:
        raise SystemExit("feedback API must not promote rules automatically")

print("OK smoke_helpus_persistent_memory_api")

