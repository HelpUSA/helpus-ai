from pathlib import Path

text = Path("backend/main.py").read_text(encoding="utf-8-sig")

required_markers = [
    "from admin_telemetry import summarize_events",
    '@app.get("/admin/telemetry")',
    "async def admin_telemetry",
    "Depends(obter_admin_google)",
    "HELPUS_TELEMETRY_LOG",
    "summarize_events(telemetry_path)",
]

missing = [marker for marker in required_markers if marker not in text]
if missing:
    raise AssertionError(f"Missing admin telemetry route markers: {missing}")

print("ADMIN_TELEMETRY_ROUTE_CONTRACT_SMOKE_OK")
