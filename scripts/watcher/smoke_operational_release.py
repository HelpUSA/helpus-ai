import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

COMMANDS = [
    [
        "python",
        "-m",
        "py_compile",
        "backend/main.py",
        "backend/banco.py",
        "backend/cerebro.py",
        "backend/command_builder.py",
        "backend/preflight_validator.py",
        "backend/intent_layer.py",
        "backend/watcher_errors.py",
        "backend/telemetry.py",
        "backend/command_safety.py",
        "backend/admin_telemetry.py",
        "scripts/watcher/smoke_behavior_ai.py",
        "scripts/watcher/smoke_intent_layer.py",
        "scripts/watcher/smoke_watcher_errors.py",
        "scripts/watcher/smoke_telemetry.py",
        "scripts/watcher/smoke_admin_telemetry.py",
        "scripts/watcher/smoke_command_safety.py",
        "scripts/watcher/smoke_watcher_stress.py",
        "scripts/watcher/smoke_memory_panel_contract.py",
    ],
    ["python", "scripts/watcher/smoke_behavior_ai.py"],
    ["python", "scripts/watcher/smoke_intent_layer.py"],
    ["python", "scripts/watcher/smoke_watcher_errors.py"],
    ["python", "scripts/watcher/smoke_telemetry.py"],
    ["python", "scripts/watcher/smoke_admin_telemetry.py"],
    ["python", "scripts/watcher/smoke_command_safety.py"],
    ["python", "scripts/watcher/smoke_watcher_stress.py"],
    ["python", "scripts/watcher/smoke_memory_panel_contract.py"],
    ["git", "diff", "--check"],
]


def run(command: list[str]) -> None:
    print("RUN", " ".join(command))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


for command in COMMANDS:
    run(command)

print("OPERATIONAL_RELEASE_SMOKE_OK")
