import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

@dataclass
class WatcherErrorRecord:
    error_type: str
    category: str
    cause: str
    correction: str
    original_command_id: str | None = None
    new_command_id: str | None = None
    raw_error: str = ""
    created_at: str = ""

class WatcherErrorClassifier:
    PARSE_MARKERS = ("envelope_parse_error", "bad escaped", "json invalido", "not valid json", "unterminated string")
    SEMANTIC_MARKERS = ("semantic_error", "missing field", "invalid delivery_kind", "invalid target_chat_id", "unknown action")
    DELIVERY_MARKERS = ("delivery_error", "chat not found", "button_click")
    TIMEOUT_MARKERS = ("timeout", "connecttimeouterror", "und_err_connect_timeout")

    @classmethod
    def classify(cls, raw_error: str) -> str:
        text = (raw_error or "").lower()
        if any(marker in text for marker in cls.PARSE_MARKERS):
            return "parse"
        if any(marker in text for marker in cls.SEMANTIC_MARKERS):
            return "semantic"
        if any(marker in text for marker in cls.TIMEOUT_MARKERS):
            return "timeout"
        if any(marker in text for marker in cls.DELIVERY_MARKERS):
            return "delivery"
        return "unknown"

    @classmethod
    def classify_record(cls, raw_error: str, original_command_id: str | None = None) -> WatcherErrorRecord:
        category = cls.classify(raw_error)
        return WatcherErrorRecord(
            error_type="watcher_error",
            category=category,
            cause="classified watcher failure",
            correction="retry with smaller validated command and new command_id",
            original_command_id=original_command_id,
            new_command_id="retry_" + uuid.uuid4().hex,
            raw_error=raw_error or "",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

@dataclass
class WatcherLearningLog:
    path: str = "logs/watcher_learning.jsonl"

    def append(self, record: WatcherErrorRecord) -> None:
        p = Path(self.path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True) + "\n")

    def load(self):
        p = Path(self.path)
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]

    def summary(self):
        counts = {}
        for record in self.load():
            category = record.get("category", "unknown")
            counts[category] = counts.get(category, 0) + 1
        return counts
