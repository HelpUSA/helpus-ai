from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "backend" / "main.py"
AUDIT = ROOT / "backend" / "local_plan_audit.py"

main_text = MAIN.read_text(encoding="utf-8")
audit_text = AUDIT.read_text(encoding="utf-8")

forbidden_endpoint_markers = [
    '@app.post("/local/execute"',
    '@app.post("/local/commands"',
    '@app.post("/local/plan/execute"',
    '@app.post("/local/plan/run"',
    '@app.post("/local/plan/approve"',
    '@app.patch("/local/plan/approve"',
]
unsafe_found = [marker for marker in forbidden_endpoint_markers if marker in main_text]

forbidden_audit_markers = [
    "subprocess.",
    "os.system(",
    "Popen(",
    "check_call(",
    "check_output(",
    "approved = True",
    '"approved": True',
    "'approved': True",
    '"executed": True',
    "'executed': True",
]
unsafe_found.extend(marker for marker in forbidden_audit_markers if marker in audit_text)

required_audit_markers = [
    'AUDIT_CONTRACT_VERSION = "local-plan-audit-v1"',
    '"mode": "proposal_only"',
    '"executed": False',
    '"approved": False',
    '"approval_status": "pending_human_review"',
    '"requires_human_confirmation": True',
]
missing_required = [marker for marker in required_audit_markers if marker not in audit_text]

if unsafe_found:
    raise SystemExit(f"unsafe executor or approval marker found: {unsafe_found}")
if missing_required:
    raise SystemExit(f"missing required audit invariants: {missing_required}")

print("SMOKE_LOCAL_EXECUTOR_ABSENT_OK")
