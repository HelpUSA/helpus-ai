from __future__ import annotations

from pathlib import Path
from typing import Any

from evolving_memory_command_store import EvolvingCommandStore
from evolving_memory_event_recorder import WatcherEventRecorder


def _payload(raw: dict[str, Any]) -> dict[str, Any]:
    return dict(raw.get("payload") or {})


class EvolvingMemoryIngestion:
    """Readonly ingestion adapter for observed watcher envelopes/results.

    This adapter persists memory only. It does not execute commands,
    call networks, expose APIs, or patch files.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.events = WatcherEventRecorder(db_path)
        self.commands = EvolvingCommandStore(db_path)

    def close(self) -> None:
        self.events.close()
        self.commands.close()

    def ingest_command_request(self, envelope: dict[str, Any]) -> dict[str, Any]:
        payload = _payload(envelope)
        command_id = str(envelope.get("command_id") or payload.get("command_id") or "")
        if not command_id:
            raise ValueError("command_id is required")

        project_id = str(payload.get("project_id") or envelope.get("conversation_id") or "helpus-ai")
        command_json = payload.get("command")
        if command_json is None:
            command_json = (
                {"script_ext": payload.get("script_ext"), "script_text": payload.get("script_text")}
                if "script_text" in payload
                else []
            )

        request = self.commands.record_command_request(
            command_id=command_id,
            project_id=project_id,
            cwd=str(payload.get("cwd") or ""),
            command_json=command_json,
            reason=str(payload.get("reason") or envelope.get("action") or "watcher command request"),
            risk_level=str(payload.get("risk_level") or envelope.get("risk_level") or "low"),
            requested_by_agent_id=payload.get("requested_by_agent_id"),
            requires_confirmation=bool(payload.get("requires_confirmation", True)),
        )
        event = self.events.record_watcher_event(
            {
                "project_id": project_id,
                "event_type": "command_request_ingested",
                "command_id": command_id,
                "status": request["status"],
                "metadata": {
                    "request_id": request["id"],
                    "delivery_kind": envelope.get("delivery_kind"),
                },
            }
        )
        return {"command_request": request, "experience_event": event}

    def ingest_command_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        command_id = str(raw.get("command_id") or raw.get("id_original") or "")
        if not command_id:
            raise ValueError("command_id is required")

        request = self.commands.get_command_request_by_command_id(command_id)
        return_code = int(raw.get("return_code") if raw.get("return_code") is not None else 0)

        result = self.commands.record_command_result(
            command_request_id=request["id"],
            return_code=return_code,
            stdout=str(raw.get("stdout") or ""),
            stderr=str(raw.get("stderr") or ""),
            files_changed_json=raw.get("files_changed_json") or raw.get("files_changed") or [],
            diff_stat=str(raw.get("diff_stat") or ""),
            summary=raw.get("summary"),
        )
        event = self.events.record_watcher_event(
            {
                "project_id": request["project_id"],
                "event_type": "command_succeeded" if return_code == 0 else "command_failed",
                "command_id": command_id,
                "return_code": return_code,
                "stdout": raw.get("stdout"),
                "stderr": raw.get("stderr"),
                "metadata": {
                    "request_id": request["id"],
                    "result_id": result["id"],
                    "status": raw.get("status"),
                },
            }
        )
        return {"command_result": result, "experience_event": event}
