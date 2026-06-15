from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.helpus_persistent_memory_store import PersistentMemoryStore


DEFAULT_LOCAL_MEMORY_DB = Path("data/helpus_persistent_memory.db")


def get_default_store() -> PersistentMemoryStore:
    return PersistentMemoryStore(DEFAULT_LOCAL_MEMORY_DB)


def memory_status_payload(store: PersistentMemoryStore | None = None) -> dict[str, Any]:
    active_store = store or get_default_store()
    return active_store.status_dict()


def recent_memory_payload(store: PersistentMemoryStore | None = None, limit: int = 20) -> dict[str, Any]:
    active_store = store or get_default_store()
    return {
        "items": active_store.list_recent_events(limit=limit),
        "limit": limit,
        "readonly": True,
    }


def create_feedback_draft_payload(
    *,
    feedback_type: str,
    source: str,
    summary: str,
    event_id: int | None = None,
    severity: str = "info",
    details: dict[str, Any] | None = None,
    store: PersistentMemoryStore | None = None,
) -> dict[str, Any]:
    active_store = store or get_default_store()
    feedback_id = active_store.record_feedback(
        feedback_type=feedback_type,
        source=source,
        summary=summary,
        event_id=event_id,
        severity=severity,
        status="draft",
        details=details or {},
    )
    return {
        "feedback_id": feedback_id,
        "status": "draft",
        "automatic_rule_promotion": False,
    }


def create_router():
    """Return a FastAPI router without wiring it automatically.

    Runtime integration must be explicit in a later guarded micro.
    """

    from fastapi import APIRouter

    router = APIRouter(prefix="/helpus/memory", tags=["helpus-memory"])

    @router.get("/status")
    def status() -> dict[str, Any]:
        return memory_status_payload()

    @router.get("/recent")
    def recent(limit: int = 20) -> dict[str, Any]:
        return recent_memory_payload(limit=limit)

    @router.post("/feedback-draft")
    def feedback_draft(payload: dict[str, Any]) -> dict[str, Any]:
        return create_feedback_draft_payload(
            feedback_type=str(payload.get("feedback_type", "operator_feedback")),
            source=str(payload.get("source", "api")),
            summary=str(payload.get("summary", "")),
            event_id=payload.get("event_id"),
            severity=str(payload.get("severity", "info")),
            details=dict(payload.get("details") or {}),
        )

    return router
