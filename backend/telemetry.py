import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

@dataclass
class TelemetryEvent:
    event_type: str
    status: str
    project_id: str = "general"
    details: dict[str, Any] | None = None
    duration_ms: float | None = None
    created_at: str = ""

class TelemetryLog:
    def __init__(self, path: str | Path = "logs/helpus_telemetry.jsonl") -> None:
        self.path = Path(path)

    def append(self, event: TelemetryEvent) -> None:
        if not event.created_at:
            event.created_at = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")

    def timed(self, event_type: str, status: str = "ok", project_id: str = "general", **details: Any) -> TelemetryEvent:
        start = time.perf_counter()
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        event = TelemetryEvent(
            event_type=event_type,
            status=status,
            project_id=project_id,
            details=details or None,
            duration_ms=duration_ms,
        )
        self.append(event)
        return event

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
