from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

AUDIT_CONTRACT_VERSION = "local-plan-audit-v1"
AUDIT_INTEGRITY_VERSION = "local-plan-audit-integrity-v1"
AUDIT_HASH_ALGORITHM = "sha256-json-v1"
PROPOSAL_STORE = Path("reports/local-plan-proposals.jsonl")
MAX_STORED_PROPOSALS = 200


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _json_ready(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _json_ready(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _proposal_id(record: dict[str, Any]) -> str:
    payload = _canonical_json(record)
    return "plan_" + sha256(payload.encode("utf-8")).hexdigest()[:16]


def _record_hash(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload.pop("record_hash", None)
    digest = sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return "sha256:" + digest


def _last_record_hash(rows: list[dict[str, Any]]) -> str | None:
    for row in reversed(rows):
        value = row.get("record_hash")
        if isinstance(value, str) and value.startswith("sha256:"):
            return value
    return None


def _read_all() -> list[dict[str, Any]]:
    if not PROPOSAL_STORE.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in PROPOSAL_STORE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _write_all(rows: list[dict[str, Any]]) -> None:
    PROPOSAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    trimmed = rows[-MAX_STORED_PROPOSALS:]
    PROPOSAL_STORE.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in trimmed),
        encoding="utf-8",
    )


def create_local_plan_proposal(payload: dict[str, Any] | None) -> dict[str, Any]:
    try:
        from backend.local_safe_plan import plan_local_action
    except ModuleNotFoundError:
        from local_safe_plan import plan_local_action

    payload = payload or {}
    plan = plan_local_action(payload)
    rows = _read_all()
    record: dict[str, Any] = {
        "ok": True,
        "mode": "proposal_only",
        "version": AUDIT_CONTRACT_VERSION,
        "integrity_version": AUDIT_INTEGRITY_VERSION,
        "integrity_algorithm": AUDIT_HASH_ALGORITHM,
        "previous_record_hash": _last_record_hash(rows),
        "created_at": _utcnow(),
        "created_by": str(payload.get("created_by") or "local-admin"),
        "note": str(payload.get("note") or ""),
        "executed": False,
        "approved": False,
        "approval_status": "pending_human_review",
        "requires_human_confirmation": True,
        "plan": _json_ready(plan),
    }
    record["proposal_id"] = _proposal_id(record)
    record["record_hash"] = _record_hash(record)
    rows.append(record)
    _write_all(rows)
    return record


def list_local_plan_proposals(limit: int = 50) -> dict[str, Any]:
    safe_limit = max(1, min(int(limit or 50), 200))
    rows = list(reversed(_read_all()))[:safe_limit]
    return {
        "ok": True,
        "mode": "proposal_only",
        "version": AUDIT_CONTRACT_VERSION,
        "integrity_version": AUDIT_INTEGRITY_VERSION,
        "executed": False,
        "count": len(rows),
        "proposals": rows,
    }


def summarize_local_plan_proposals(limit: int = MAX_STORED_PROPOSALS) -> dict[str, Any]:
    try:
        safe_limit = int(limit)
    except (TypeError, ValueError):
        safe_limit = MAX_STORED_PROPOSALS
    safe_limit = max(1, min(safe_limit, MAX_STORED_PROPOSALS))

    rows = _read_all()
    selected = rows[-safe_limit:]

    def bump(bucket: dict[str, int], value: Any) -> None:
        key = str(value or "unknown")
        bucket[key] = bucket.get(key, 0) + 1

    by_intent: dict[str, int] = {}
    by_created_by: dict[str, int] = {}
    by_approval_status: dict[str, int] = {}
    by_mode: dict[str, int] = {}

    pending_human_review = 0
    requires_human_confirmation = 0

    for row in selected:
        plan = row.get("plan") if isinstance(row.get("plan"), dict) else {}
        bump(by_intent, plan.get("intent") or row.get("intent"))
        bump(by_created_by, row.get("created_by"))
        bump(by_approval_status, row.get("approval_status"))
        bump(by_mode, row.get("mode"))

        if row.get("approval_status") == "pending_human_review":
            pending_human_review += 1
        if row.get("requires_human_confirmation") is True:
            requires_human_confirmation += 1

    latest = selected[-1] if selected else None

    return {
        "ok": True,
        "mode": "proposal_only",
        "version": AUDIT_CONTRACT_VERSION,
        "integrity_version": AUDIT_INTEGRITY_VERSION,
        "integrity_algorithm": AUDIT_HASH_ALGORITHM,
        "executed": False,
        "approved": False,
        "count": len(rows),
        "summarized": len(selected),
        "limit": safe_limit,
        "by_intent": by_intent,
        "by_created_by": by_created_by,
        "by_approval_status": by_approval_status,
        "by_mode": by_mode,
        "pending_human_review": pending_human_review,
        "requires_human_confirmation": requires_human_confirmation,
        "latest_created_at": latest.get("created_at") if latest else None,
        "latest_proposal_id": latest.get("proposal_id") if latest else None,
        "latest_record_hash": latest.get("record_hash") if latest else None,
    }

def verify_local_plan_proposal_integrity() -> dict[str, Any]:
    rows = _read_all()
    errors: list[dict[str, Any]] = []
    previous_hash: str | None = None
    checked = 0
    legacy = 0

    for index, row in enumerate(rows):
        row_hash = row.get("record_hash")
        if not isinstance(row_hash, str) or not row_hash.startswith("sha256:"):
            legacy += 1
            previous_hash = None
            continue

        expected_hash = _record_hash(row)
        actual_previous = row.get("previous_record_hash")

        if row_hash != expected_hash:
            errors.append(
                {
                    "index": index,
                    "proposal_id": row.get("proposal_id"),
                    "field": "record_hash",
                    "expected": expected_hash,
                    "actual": row_hash,
                }
            )

        if checked > 0 and actual_previous != previous_hash:
            errors.append(
                {
                    "index": index,
                    "proposal_id": row.get("proposal_id"),
                    "field": "previous_record_hash",
                    "expected": previous_hash,
                    "actual": actual_previous,
                }
            )

        checked += 1
        previous_hash = row_hash

    return {
        "ok": len(errors) == 0,
        "mode": "proposal_only",
        "version": AUDIT_CONTRACT_VERSION,
        "integrity_version": AUDIT_INTEGRITY_VERSION,
        "integrity_algorithm": AUDIT_HASH_ALGORITHM,
        "executed": False,
        "approved": False,
        "count": len(rows),
        "checked": checked,
        "legacy_count": legacy,
        "errors": errors,
    }
