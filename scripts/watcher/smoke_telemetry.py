import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "backend"))

from telemetry import TelemetryLog

tmp = ROOT / "temp" / "telemetry_smoke.jsonl"
tmp.parent.mkdir(exist_ok=True)
tmp.unlink(missing_ok=True)

log = TelemetryLog(tmp)
event = log.timed("smoke", status="ok", project_id="helpusai", source="test")
records = log.load()

assert event.event_type == "smoke"
assert len(records) == 1
assert records[0]["event_type"] == "smoke"
assert records[0]["project_id"] == "helpusai"
assert records[0]["details"]["source"] == "test"

tmp.unlink(missing_ok=True)
print("TELEMETRY_SMOKE_OK")
