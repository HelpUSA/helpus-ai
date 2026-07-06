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
    assert_true(proposal["executed"] is False, proposal)
    assert_true(proposal["approved"] is False, proposal)
    assert_true(proposal["approval_status"] == "pending_human_review", proposal)
    assert_true(proposal["requires_human_confirmation"] is True, proposal)
    assert_true(proposal["version"] == audit.AUDIT_CONTRACT_VERSION, proposal)
    assert_true(proposal["integrity_version"] == audit.AUDIT_INTEGRITY_VERSION, proposal)
    assert_true(proposal["integrity_algorithm"] == audit.AUDIT_HASH_ALGORITHM, proposal)
    assert_true(proposal["previous_record_hash"] is None, proposal)
    assert_true(str(proposal["record_hash"]).startswith("sha256:"), proposal)
    assert_true(proposal["plan"]["executed"] is False, proposal)
    assert_true("commands" in proposal["plan"], proposal)

    second = audit.create_local_plan_proposal({
        "intent": "local_status",
        "created_by": "smoke",
        "note": "second proposal",
    })
    assert_true(second["previous_record_hash"] == proposal["record_hash"], second)

    proposals = audit.list_local_plan_proposals(limit=10)
    assert_true(proposals["ok"] is True, proposals)
    assert_true(proposals["mode"] == "proposal_only", proposals)
    assert_true(proposals["executed"] is False, proposals)
    assert_true(proposals["count"] == 2, proposals)
    assert_true(proposals["proposals"][0]["proposal_id"] == second["proposal_id"], proposals)
    assert_true(proposals["proposals"][1]["proposal_id"] == proposal["proposal_id"], proposals)

    integrity = audit.verify_local_plan_proposal_integrity()
    assert_true(integrity["ok"] is True, integrity)
    assert_true(integrity["checked"] == 2, integrity)
    assert_true(integrity["legacy_count"] == 0, integrity)
    assert_true(integrity["executed"] is False, integrity)
    assert_true(integrity["approved"] is False, integrity)

print("SMOKE_LOCAL_PLAN_AUDIT_OK")
