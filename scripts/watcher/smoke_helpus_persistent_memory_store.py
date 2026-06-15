from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import tempfile

from backend.helpus_persistent_memory_store import PersistentMemoryStore

with tempfile.TemporaryDirectory() as tmp:
    db_path = Path(tmp) / "memory.db"
    store = PersistentMemoryStore(db_path)

    before = store.status_dict()
    if before["event_count"] != 0:
        raise SystemExit("expected empty event count")

    event_id = store.record_event(
        event_type="conversation_test",
        source="smoke",
        conversation_id="smoke-conversation",
        actor="operator",
        summary="Recorded a smoke event",
        details={"safe": True},
    )

    if event_id < 1:
        raise SystemExit("invalid event id")

    feedback_id = store.record_feedback(
        event_id=event_id,
        feedback_type="operator_feedback",
        source="smoke",
        summary="Keep feedback as draft",
        details={"automatic_rule_promotion": False},
    )

    if feedback_id < 1:
        raise SystemExit("invalid feedback id")

    events = store.list_recent_events()
    if len(events) != 1:
        raise SystemExit("expected one event")
    if events[0]["details"]["safe"] is not True:
        raise SystemExit("details JSON did not roundtrip")

    feedback = store.list_draft_feedback()
    if len(feedback) != 1:
        raise SystemExit("expected one draft feedback")
    if feedback[0]["status"] != "draft":
        raise SystemExit("feedback must be draft")

    after = store.status_dict()
    if after["event_count"] != 1 or after["feedback_count"] != 1:
        raise SystemExit("status counts mismatch")
    if after["ready_for_production_migration"] is not False:
        raise SystemExit("production migration must not be auto-ready")

print("OK smoke_helpus_persistent_memory_store")

