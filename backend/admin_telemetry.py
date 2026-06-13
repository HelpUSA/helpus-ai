import json
from pathlib import Path
from typing import Any


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def summarize_events(path: str | Path) -> dict[str, Any]:
    records = load_jsonl(path)
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_project: dict[str, int] = {}

    for record in records:
        event_type = str(record.get("event_type") or "unknown")
        status = str(record.get("status") or "unknown")
        project_id = str(record.get("project_id") or "general")
        by_type[event_type] = by_type.get(event_type, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        by_project[project_id] = by_project.get(project_id, 0) + 1

    return {
        "total": len(records),
        "by_type": by_type,
        "by_status": by_status,
        "by_project": by_project,
    }
