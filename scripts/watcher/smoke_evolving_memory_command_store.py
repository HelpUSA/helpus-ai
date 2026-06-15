from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from evolving_memory_command_store import EvolvingCommandStore


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = (ROOT / "backend" / "evolving_memory_command_store.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "command store must not execute commands")
    assert_true("import requests" not in source, "command store must not import requests")

    with tempfile.TemporaryDirectory() as tmp:
        store = EvolvingCommandStore(Path(tmp) / "memory.sqlite")
        request = store.record_command_request(request_id="req-1", command_id="cmd-1", project_id="helpus-ai", cwd="D:/dev/ai", command_json=["git", "status", "-sb"], reason="readonly status", risk_level="low", requires_confirmation=False)
        assert_true(request["id"] == "req-1", "request id persisted")
        assert_true(json.loads(request["command_json"])[0] == "git", "command json persisted")
        assert_true(request["requires_confirmation"] == 0, "requires_confirmation persisted")

        try:
            store.record_command_request(command_id="cmd-1", project_id="helpus-ai", cwd="D:/dev/ai", command_json=[], reason="duplicate", risk_level="low")
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("duplicate command_id accepted")

        result = store.record_command_result(result_id="res-1", command_request_id="req-1", return_code=0, stdout="ok", stderr="", files_changed_json=[], diff_stat="", summary="passed")
        assert_true(result["command_request_id"] == "req-1", "result references request")
        assert_true(store.get_command_request_by_command_id("cmd-1")["id"] == "req-1", "lookup by command_id works")
        assert_true(len(store.list_command_requests(project_id="helpus-ai", limit=10)) == 1, "request list works")
        assert_true(len(store.list_command_results_for_request("req-1")) == 1, "result list works")

        try:
            store.record_command_result(command_request_id="missing", return_code=1)
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("orphan command_result accepted")

        try:
            store.record_command_request(command_id="cmd-2", project_id="helpus-ai", cwd="D:/dev/ai", command_json=[], reason="bad risk", risk_level="danger")
        except ValueError:
            pass
        else:
            raise AssertionError("bad risk_level accepted")

        store.close()

    print("EVOLVING_MEMORY_COMMAND_STORE_SMOKE_OK")


if __name__ == "__main__":
    main()

