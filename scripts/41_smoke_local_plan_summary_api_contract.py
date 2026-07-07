from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import local_plan_audit as audit

main_text = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
audit_text = (ROOT / "backend" / "local_plan_audit.py").read_text(encoding="utf-8")

required_main = [
    '@app.get("/local/plan/proposals/summary")',
    "async def local_plan_proposal_summary",
    "summarize_local_plan_proposals",
    "return summarize_local_plan_proposals(limit)",
]
missing = [marker for marker in required_main if marker not in main_text]
if missing:
    raise SystemExit("missing summary API markers: " + ", ".join(missing))

for method in ["post", "put", "patch", "delete"]:
    marker = '@app.' + method + '("/local/plan/proposals/summary")'
    if marker in main_text:
        raise SystemExit("summary endpoint must remain GET/read-only; found " + marker)

for forbidden in [
    '"/local/execute"',
    '"/local/commands"',
    '"/local/plan/execute"',
    '"/local/plan/run"',
    '"/local/plan/approve"',
]:
    if forbidden in main_text:
        raise SystemExit("unsafe local endpoint marker found in backend/main.py: " + forbidden)

for forbidden_call in ["subprocess.", "os.system(", "Popen(", "check_call(", "check_output("]:
    if forbidden_call in audit_text:
        raise SystemExit("audit module must not execute commands; found " + forbidden_call)

with tempfile.TemporaryDirectory() as tmp:
    audit.PROPOSAL_STORE = Path(tmp) / "local-plan-proposals.jsonl"

    first = audit.create_local_plan_proposal({
        "intent": "local_status",
        "created_by": "summary-api-smoke",
        "note": "first summary contract proposal",
    })
    second = audit.create_local_plan_proposal({
        "intent": "local_diff",
        "created_by": "summary-api-smoke",
        "note": "second summary contract proposal",
    })
    third = audit.create_local_plan_proposal({
        "intent": "local_status",
        "created_by": "another-summary-smoke",
        "note": "third summary contract proposal",
    })

    before = audit.PROPOSAL_STORE.read_text(encoding="utf-8")
    summary = audit.summarize_local_plan_proposals(limit=10)
    after = audit.PROPOSAL_STORE.read_text(encoding="utf-8")

    if before != after:
        raise SystemExit("summary must not mutate the proposal store")

    expected = {
        "ok": True,
        "mode": "proposal_only",
        "version": audit.AUDIT_CONTRACT_VERSION,
        "integrity_version": audit.AUDIT_INTEGRITY_VERSION,
        "integrity_algorithm": audit.AUDIT_HASH_ALGORITHM,
        "executed": False,
        "approved": False,
        "count": 3,
        "summarized": 3,
        "pending_human_review": 3,
        "requires_human_confirmation": 3,
        "latest_proposal_id": third["proposal_id"],
        "latest_record_hash": third["record_hash"],
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise SystemExit(f"summary field {key!r} drifted: {summary!r}")

    if summary["by_intent"] != {"local_status": 2, "local_diff": 1}:
        raise SystemExit("summary by_intent drifted: " + repr(summary))
    if summary["by_created_by"] != {"summary-api-smoke": 2, "another-summary-smoke": 1}:
        raise SystemExit("summary by_created_by drifted: " + repr(summary))
    if summary["by_approval_status"] != {"pending_human_review": 3}:
        raise SystemExit("summary by_approval_status drifted: " + repr(summary))
    if summary["by_mode"] != {"proposal_only": 3}:
        raise SystemExit("summary by_mode drifted: " + repr(summary))

    limited = audit.summarize_local_plan_proposals(limit=2)
    if limited["count"] != 3 or limited["summarized"] != 2:
        raise SystemExit("summary limit handling drifted: " + repr(limited))
    if limited["by_intent"] != {"local_diff": 1, "local_status": 1}:
        raise SystemExit("summary limited by_intent drifted: " + repr(limited))

print("SMOKE_LOCAL_PLAN_SUMMARY_API_CONTRACT_OK")
