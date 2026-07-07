from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import local_plan_audit as audit

main_text = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
audit_text = (ROOT / "backend" / "local_plan_audit.py").read_text(encoding="utf-8")

required = [
    '@app.get("/local/plan/proposals/verify")',
    "async def get_local_plan_proposal_integrity",
    "verify_local_plan_proposal_integrity",
    "return verify_local_plan_proposal_integrity()",
]
missing = [marker for marker in required if marker not in main_text]
if missing:
    raise SystemExit("missing verify API markers: " + ", ".join(missing))

for method in ["post", "put", "patch", "delete"]:
    marker = '@app.' + method + '("/local/plan/proposals/verify")'
    if marker in main_text:
        raise SystemExit("verify endpoint must remain GET/read-only; found " + marker)

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
        "created_by": "verify-api-contract-smoke",
        "note": "first verify api contract proposal",
    })
    second = audit.create_local_plan_proposal({
        "intent": "local_diff",
        "created_by": "verify-api-contract-smoke",
        "note": "second verify api contract proposal",
    })

    verify = audit.verify_local_plan_proposal_integrity()

    if verify["ok"] is not True:
        raise SystemExit("verify result should be ok for clean store: " + repr(verify))
    if verify["mode"] != "proposal_only":
        raise SystemExit("verify mode drifted: " + repr(verify))
    if verify["version"] != audit.AUDIT_CONTRACT_VERSION:
        raise SystemExit("verify contract version drifted: " + repr(verify))
    if verify["integrity_version"] != audit.AUDIT_INTEGRITY_VERSION:
        raise SystemExit("verify integrity version drifted: " + repr(verify))
    if verify["integrity_algorithm"] != audit.AUDIT_HASH_ALGORITHM:
        raise SystemExit("verify hash algorithm drifted: " + repr(verify))
    if verify["executed"] is not False or verify["approved"] is not False:
        raise SystemExit("verify response must not mark execution/approval: " + repr(verify))
    if verify["count"] != 2 or verify["checked"] != 2 or verify["legacy_count"] != 0:
        raise SystemExit("verify counts drifted: " + repr(verify))
    if verify["errors"] != []:
        raise SystemExit("verify errors should be empty: " + repr(verify))

    for proposal in [first, second]:
        if proposal["executed"] is not False or proposal["approved"] is not False:
            raise SystemExit("proposal must stay proposal-only: " + repr(proposal))
        if proposal["approval_status"] != "pending_human_review":
            raise SystemExit("proposal approval status drifted: " + repr(proposal))
        if proposal["requires_human_confirmation"] is not True:
            raise SystemExit("proposal human confirmation flag drifted: " + repr(proposal))
        if not str(proposal["record_hash"]).startswith("sha256:"):
            raise SystemExit("proposal record_hash missing: " + repr(proposal))

    if second["previous_record_hash"] != first["record_hash"]:
        raise SystemExit("hash chain previous_record_hash mismatch")

    before = audit.PROPOSAL_STORE.read_text(encoding="utf-8")
    verify_again = audit.verify_local_plan_proposal_integrity()
    after = audit.PROPOSAL_STORE.read_text(encoding="utf-8")
    if after != before:
        raise SystemExit("verify must not mutate the proposal store")
    if verify_again["ok"] is not True:
        raise SystemExit("verify_again should remain ok: " + repr(verify_again))

print("SMOKE_LOCAL_PLAN_VERIFY_API_CONTRACT_OK")
