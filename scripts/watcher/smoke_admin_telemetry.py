import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "backend"))

from telemetry import TelemetryLog
from admin_telemetry import summarize_events

tmp = ROOT / "temp" / "admin_telemetry_smoke.jsonl"
tmp.parent.mkdir(exist_ok=True)
tmp.unlink(missing_ok=True)

log = TelemetryLog(tmp)
log.timed("smoke", status="ok", project_id="helpusai", source="admin")
log.timed("provider_check", status="failed", project_id="helpusai", source="admin")

summary = summarize_events(tmp)
assert summary["total"] == 2
assert summary["by_type"]["smoke"] == 1
assert summary["by_type"]["provider_check"] == 1
assert summary["by_status"]["ok"] == 1
assert summary["by_status"]["failed"] == 1
assert summary["by_project"]["helpusai"] == 2

tmp.unlink(missing_ok=True)
print("ADMIN_TELEMETRY_SMOKE_OK")
