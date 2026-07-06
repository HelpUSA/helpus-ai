from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import local_plan_audit as audit


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


with tempfile.TemporaryDirectory() as tmp:
    audit.PROPOSAL_STORE = Path(tmp) / "local-plan-proposals.jsonl"

    proposal = audit.create_local_plan_proposal({
        "intent": "phase_b_validation",
        "created_by": "smoke",
        "note": "contract smoke",
    })
    assert_true(proposal["ok"] is True, proposal)
    assert_true(proposal["mode"] == "proposal_only", proposal)
    assert_true(proposal["version"] == "local-plan-audit-v1", proposal)
    assert_true(proposal["executed"] is False, proposal)
    assert_true(proposal["approved"] is False, proposal)
    assert_true(proposal["approval_status"] == "pending_human_review", proposal)
    assert_true(proposal["requires_human_confirmation"] is True, proposal)
    assert_true(proposal["plan"]["executed"] is False, proposal)
    assert_true(proposal["plan"]["commands"] == ["npm run smoke:phase-b"], proposal)
    assert_true(proposal["proposal_id"].startswith("plan_"), proposal)

    blocked = audit.create_local_plan_proposal({"command": "git push origin main", "created_by": "smoke"})
    assert_true(blocked["plan"]["risk"] == "blocked", blocked)
    assert_true(blocked["executed"] is False, blocked)

    listed = audit.list_local_plan_proposals(limit=10)
    assert_true(listed["ok"] is True, listed)
    assert_true(listed["mode"] == "proposal_only", listed)
    assert_true(listed["executed"] is False, listed)
    assert_true(listed["count"] == 2, listed)
    assert_true(listed["proposals"][0]["proposal_id"] == blocked["proposal_id"], listed)

main_text = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
assert_true('@app.post("/local/plan/proposals")' in main_text, "missing proposal create endpoint")
assert_true('@app.get("/local/plan/proposals")' in main_text, "missing proposal list endpoint")

print("SMOKE_LOCAL_PLAN_AUDIT_OK")
