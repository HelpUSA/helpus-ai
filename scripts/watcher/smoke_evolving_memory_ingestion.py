from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from evolving_memory_ingestion import EvolvingMemoryIngestion


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = (ROOT / "backend" / "evolving_memory_ingestion.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "ingestion must not execute commands")
    assert_true("import requests" not in source, "ingestion must not import requests")

    with tempfile.TemporaryDirectory() as tmp:
        ingestion = EvolvingMemoryIngestion(Path(tmp) / "memory.sqlite")
        request_pack = ingestion.ingest_command_request(
            {
                "command_id": "cmd-1",
                "action": "run-command",
                "delivery_kind": "local_capability",
                "payload": {
                    "project_id": "helpus-ai",
                    "cwd": "D:/dev/ai",
                    "command": ["git", "status", "-sb"],
                    "reason": "readonly inspect",
                    "risk_level": "low",
                    "requires_confirmation": False,
                },
            }
        )
        request = request_pack["command_request"]
        assert_true(request["command_id"] == "cmd-1", "command request ingested")
        assert_true(json.loads(request["command_json"])[0] == "git", "command json persisted")
        assert_true(request_pack["experience_event"]["event_type"] == "command_request_ingested", "request event recorded")

        result_pack = ingestion.ingest_command_result(
            {
                "command_id": "cmd-1",
                "return_code": 1,
                "status": "failed",
                "stdout": "ok token=supersecret",
                "stderr": "Authorization: bearer abcdefghijklmnop",
                "summary": "failed with secret",
            }
        )
        result = result_pack["command_result"]
        assert_true(result["command_request_id"] == request["id"], "result references request")
        assert_true("supersecret" not in result["stdout"], "stdout sanitized by command store")
        assert_true("abcdefghijklmnop" not in result["stderr"], "stderr sanitized by command store")
        assert_true(result_pack["experience_event"]["event_type"] == "command_failed", "result event recorded")

        try:
            ingestion.ingest_command_result({"command_id": "missing", "return_code": 0})
        except KeyError:
            pass
        else:
            raise AssertionError("orphan result accepted")
        ingestion.close()

    print("EVOLVING_MEMORY_INGESTION_SMOKE_OK")


if __name__ == "__main__":
    main()
