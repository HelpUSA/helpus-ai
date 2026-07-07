from pathlib import Path
import sys
import tempfile

ROOT = Path.cwd()
if str(ROOT) not in sys.path:
 sys.path.insert(0, str(ROOT))

import backend.local_plan_audit as audit
from backend.local_plan_audit import create_local_plan_proposal, get_local_plan_proposal

ROOT = Path(__file__).resolve().parents[1]

MAIN = ROOT / "backend" / "main.py"
AUDIT = ROOT / "backend" / "local_plan_audit.py"

main_text = MAIN.read_text(encoding="utf-8")
audit_text = AUDIT.read_text(encoding="utf-8")

required_main = [
    '@app.get("/local/plan/proposals/{proposal_id}")',
    "local_plan_proposal_detail",
    "get_local_plan_proposal(proposal_id)",
]
missing_main = [marker for marker in required_main if marker not in main_text]
if missing_main:
    raise SystemExit("missing detail API markers: " + ", ".join(missing_main))

summary_index = main_text.find('/local/plan/proposals/summary')
verify_index = main_text.find('/local/plan/proposals/verify')
detail_index = main_text.find('/local/plan/proposals/{proposal_id}')
if summary_index < 0 or verify_index < 0 or detail_index < 0:
    raise SystemExit("missing proposal route order markers")
if not (summary_index < detail_index and verify_index < detail_index):
    raise SystemExit("dynamic detail route must be declared after static summary/verify routes")

for forbidden in [
    '@app.post("/local/plan/proposals/{proposal_id}")',
    '@app.put("/local/plan/proposals/{proposal_id}")',
    '@app.patch("/local/plan/proposals/{proposal_id}")',
    '@app.delete("/local/plan/proposals/{proposal_id}")',
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    if forbidden in main_text:
        raise SystemExit("unsafe or mutating route marker found: " + forbidden)

if "def get_local_plan_proposal(" not in audit_text:
    raise SystemExit("missing get_local_plan_proposal function")

fn_start = audit_text.find("def get_local_plan_proposal(")
next_def = audit_text.find("\ndef ", fn_start + 1)
fn_body = audit_text[fn_start:] if next_def < 0 else audit_text[fn_start:next_def]

for required in [
    "_read_all()",
    '"mode": "proposal_only"',
    '"executed": False',
    '"approved": False',
    '"found": proposal is not None',
    '"proposal": proposal',
]:
    if required not in fn_body:
        raise SystemExit("missing detail function marker: " + required)

for forbidden in [
    "_write_all",
    "PROPOSAL_STORE.write_text",
    "subprocess.",
    "os.system(",
    "Popen(",
    "check_call(",
    "check_output(",
]:
    if forbidden in fn_body:
        raise SystemExit("mutating or executor marker found in detail function: " + forbidden)

with tempfile.TemporaryDirectory() as tmp:
    original_store = audit.PROPOSAL_STORE
    audit.PROPOSAL_STORE = Path(tmp) / "local-plan-proposals.jsonl"
    try:
        first = create_local_plan_proposal({"intent": "local_status", "created_by": "phase_i_detail_smoke"})
        second = create_local_plan_proposal({"intent": "local_recent_commits", "created_by": "phase_i_detail_smoke"})

        before = audit.PROPOSAL_STORE.read_text(encoding="utf-8")

        detail = get_local_plan_proposal(second["proposal_id"])
        if not detail.get("ok"):
            raise SystemExit("detail ok flag is false")
        if detail.get("mode") != "proposal_only":
            raise SystemExit("detail mode is not proposal_only")
        if detail.get("executed") is not False or detail.get("approved") is not False:
            raise SystemExit("detail response must remain unexecuted/unapproved")
        if detail.get("found") is not True:
            raise SystemExit("detail did not find existing proposal")
        if detail.get("proposal_id") != second["proposal_id"]:
            raise SystemExit("detail proposal_id mismatch")
        if not isinstance(detail.get("proposal"), dict):
            raise SystemExit("detail proposal is not an object")
        if detail["proposal"].get("proposal_id") != second["proposal_id"]:
            raise SystemExit("detail returned wrong proposal")
        if detail["proposal"].get("proposal_id") == first["proposal_id"]:
            raise SystemExit("detail returned older proposal unexpectedly")

        missing = get_local_plan_proposal("plan_missing")
        if missing.get("found") is not False:
            raise SystemExit("missing detail should have found=false")
        if missing.get("proposal") is not None:
            raise SystemExit("missing detail should have proposal=null")
        if missing.get("executed") is not False or missing.get("approved") is not False:
            raise SystemExit("missing detail must remain unexecuted/unapproved")

        after = audit.PROPOSAL_STORE.read_text(encoding="utf-8")
        if before != after:
            raise SystemExit("detail lookup mutated proposal store")
    finally:
        audit.PROPOSAL_STORE = original_store

print("SMOKE_LOCAL_PLAN_DETAIL_API_CONTRACT_OK")
