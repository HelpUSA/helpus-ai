from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = [
    ROOT / "docs" / "HELPUS_PROJECT_MASTER.md",
    ROOT / "docs" / "legacy" / "HELPUS_WATCHER_COMMAND_PROTOCOL.md",
]


def read_docs() -> str:
    parts = []
    for path in CANDIDATES:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8-sig", errors="replace"))
    if not parts:
        raise AssertionError("Missing HelpUS watcher command protocol documentation")
    return "\n".join(parts)


def assert_contains(text: str, marker: str) -> None:
    if marker not in text:
        raise AssertionError("Missing marker: " + marker)


text = read_docs()
assert_contains(text, "watcher")
assert_contains(text, "AI_LOCAL")
assert_contains(text, "run-command")
assert_contains(text, "send-chat-message")
print("WATCHER_COMMAND_PROTOCOL_SMOKE_OK")
