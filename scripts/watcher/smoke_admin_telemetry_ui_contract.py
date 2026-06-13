from pathlib import Path

text = Path("frontend/src/app/admin/page.tsx").read_text(encoding="utf-8-sig")

required = [
    "interface TelemetrySummary",
    "function formatTelemetryMap",
    "const [telemetryData, setTelemetryData]",
    "/admin/telemetry",
    "Telemetria operacional",
    "telemetryData?.total",
    "telemetryData?.by_status",
    "telemetryData?.by_type",
    "telemetryData?.by_project",
]

missing = [item for item in required if item not in text]
if missing:
    raise AssertionError(f"Missing admin telemetry UI markers: {missing}")

print("ADMIN_TELEMETRY_UI_CONTRACT_SMOKE_OK")
