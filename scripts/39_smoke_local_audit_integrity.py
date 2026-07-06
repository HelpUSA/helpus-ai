from pathlib import Path
import json
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

    first = audit.create_local_plan_proposal({"intent": "local_status", "created_by": "integrity-smoke"})
    second = audit.create_local_plan_proposal({"intent": "local_diff", "created_by": "integrity-smoke"})

    assert_true(first["record_hash"].startswith("sha256:"), first)
    assert_true(second["previous_record_hash"] == first["record_hash"], second)

    clean = audit.verify_local_plan_proposal_integrity()
    assert_true(clean["ok"] is True, clean)
    assert_true(clean["checked"] == 2, clean)
    assert_true(clean["errors"] == [], clean)

    rows = [
        json.loads(line)
        for line in audit.PROPOSAL_STORE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows[0]["note"] = "tampered after hash"
    audit.PROPOSAL_STORE.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )

    tampered = audit.verify_local_plan_proposal_integrity()
    assert_true(tampered["ok"] is False, tampered)
    assert_true(any(error["field"] == "record_hash" for error in tampered["errors"]), tampered)
    assert_true(tampered["executed"] is False, tampered)
    assert_true(tampered["approved"] is False, tampered)

print("SMOKE_LOCAL_PLAN_AUDIT_INTEGRITY_OK")
