import json
import subprocess
from pathlib import Path

ROOT = Path.cwd()
report = ROOT / "reports" / "helpus_health_report.json"
if report.exists():
    report.unlink()

subprocess.check_call(["python", "scripts/watcher/health_report.py"], cwd=ROOT)

data = json.loads(report.read_text(encoding="utf-8"))
assert data["project"] == "HelpUS AI"
assert data["git_status"]["returncode"] == 0
assert data["git_head"]["returncode"] == 0
assert isinstance(data["smoke_files"], list)
assert any(
    item["path"].endswith("smoke_operational_release.py") and item["exists"]
    for item in data["smoke_files"]
)

print("HEALTH_REPORT_SMOKE_OK")
