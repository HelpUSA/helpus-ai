from pathlib import Path

path = Path("docs/HELPUS_WATCHER_COMMAND_PROTOCOL.md")
text = path.read_text(encoding="utf-8-sig")

required = [
    "HelpUS Watcher Command Protocol",
    "Recibos nao sao comandos de entrada",
    "@@AI_BRIDGE_LOCAL_START@@",
    "@@AI_BRIDGE_LOCAL_END@@",
    "payload.command",
    "envelope_parse_error",
    "python scripts/watcher/smoke_operational_release.py",
    "python scripts/watcher/smoke_health_report.py",
    "npm --prefix frontend run build",
    "git diff --check",
    "git reset --hard",
    "git clean -fd",
    "deploy",
    "dry-run",
]

missing = [item for item in required if item not in text]
if missing:
    raise AssertionError(f"Missing watcher command protocol markers: {missing}")

print("WATCHER_COMMAND_PROTOCOL_SMOKE_OK")
