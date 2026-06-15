from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from evolving_memory_store import EvolvingMemoryStore


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = (ROOT / "backend" / "evolving_memory_store.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "store must not execute commands")
    assert_true("requests" not in source, "store must not make network requests")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "memory.sqlite"
        store = EvolvingMemoryStore(db_path)

        event = store.record_experience_event(
            event_id="event-1",
            project_id="helpus-ai",
            event_type="watcher_error_received",
            input_text="composer_not_empty_before_inject",
            output_text="retry later",
            metadata={"micro": 2, "mode": "readonly"},
        )
        assert_true(event["id"] == "event-1", "event id persisted")
        assert_true(event["project_id"] == "helpus-ai", "project persisted")
        assert_true(event["event_type"] == "watcher_error_received", "event type persisted")
        assert_true(json.loads(event["metadata_json"])["micro"] == 2, "metadata persisted")
        assert_true(store.count_experience_events(project_id="helpus-ai") == 1, "project count")

        store.record_experience_event(
            project_id="helpus-ai",
            event_type="command_succeeded",
            metadata={"smoke": True},
        )
        store.record_experience_event(
            project_id="other-project",
            event_type="command_succeeded",
            metadata={"smoke": True},
        )

        helpus_events = store.list_experience_events(project_id="helpus-ai", limit=10)
        assert_true(len(helpus_events) == 2, "project filter returns two events")

        watcher_errors = store.list_experience_events(
            project_id="helpus-ai",
            event_type="watcher_error_received",
            limit=10,
        )
        assert_true(len(watcher_errors) == 1, "event type filter returns one event")

        try:
            store.list_experience_events(limit=0)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid limit accepted")

        store.close()

        reopened = EvolvingMemoryStore(db_path)
        assert_true(
            reopened.count_experience_events(project_id="helpus-ai") == 2,
            "events persist on disk",
        )
        reopened.close()

    print("EVOLVING_MEMORY_STORE_SMOKE_OK")


if __name__ == "__main__":
    main()
