from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

AUDIT_CONTRACT_VERSION = "local-plan-audit-v1"
PROPOSAL_STORE = Path("reports/local-plan-proposals.jsonl")
MAX_STORED_PROPOSALS = 200


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _json_ready(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))


def _proposal_id(record: dict[str, Any]) -> str:
    payload = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
    return "plan_" + sha256(payload.encode("utf-8")).hexdigest()[:16]


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
    record: dict[str, Any] = {
        "ok": True,
        "mode": "proposal_only",
        "version": AUDIT_CONTRACT_VERSION,
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
    rows = _read_all()
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
        "executed": False,
        "count": len(rows),
        "proposals": rows,
    }
