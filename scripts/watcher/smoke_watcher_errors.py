import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "backend"))

from watcher_errors import WatcherErrorClassifier, WatcherLearningLog

assert WatcherErrorClassifier.classify("envelope_parse_error bad escaped") == "parse"
assert WatcherErrorClassifier.classify("invalid delivery_kind") == "semantic"
assert WatcherErrorClassifier.classify("ConnectTimeoutError UND_ERR_CONNECT_TIMEOUT") == "timeout"
assert WatcherErrorClassifier.classify("delivery_error chat not found") == "delivery"
assert WatcherErrorClassifier.classify("unexpected failure") == "unknown"

record = WatcherErrorClassifier.classify_record("envelope_parse_error", "cmd_old")
assert record.new_command_id and record.new_command_id.startswith("retry_")

tmp = ROOT / "temp" / "watcher_learning_smoke.jsonl"
tmp.parent.mkdir(exist_ok=True)
tmp.unlink(missing_ok=True)

log = WatcherLearningLog(str(tmp))
log.append(record)
log.append(WatcherErrorClassifier.classify_record("ConnectTimeoutError"))
summary = log.summary()
assert summary.get("parse") == 1
assert summary.get("timeout") == 1

tmp.unlink(missing_ok=True)
print("WATCHER_ERRORS_SMOKE_OK")
