import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()

SMOKE_FILES = [
    "scripts/watcher/smoke_behavior_ai.py",
    "scripts/watcher/smoke_intent_layer.py",
    "scripts/watcher/smoke_watcher_errors.py",
    "scripts/watcher/smoke_telemetry.py",
    "scripts/watcher/smoke_admin_telemetry.py",
    "scripts/watcher/smoke_admin_telemetry_route_contract.py",
    "scripts/watcher/smoke_admin_telemetry_ui_contract.py",
    "scripts/watcher/smoke_command_safety.py",
    "scripts/watcher/smoke_watcher_stress.py",
    "scripts/watcher/smoke_memory_panel_contract.py",
    "scripts/watcher/smoke_operational_release.py",
]

def run(command: list[str]) -> dict:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }

def build_report() -> dict:
    return {
        "project": "HelpUS AI",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_status": run(["git", "status", "-sb"]),
        "git_head": run(["git", "rev-parse", "--short", "HEAD"]),
        "git_log": run(["git", "log", "--oneline", "--decorate", "-8"]),
        "smoke_files": [
            {"path": item, "exists": (ROOT / item).exists()}
            for item in SMOKE_FILES
        ],
    }

def main() -> None:
    output = ROOT / "reports" / "helpus_health_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_report(), indent=2, ensure_ascii=False) + chr(10),
        encoding="utf-8",
    )
    print("HEALTH_REPORT_OK", output.as_posix())

main()
