import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "helpusai"))

import export_obsidian_vault as exporter


def check(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    written = exporter.export_vault()

    expected = {
        "Home.md",
        "Operational Lessons.md",
        "AI Bridge Local.md",
        "Watcher Protocol.md",
        "HelpUSAI Memory.md",
    }

    names = {path.name for path in written}
    check(expected.issubset(names), "missing expected Obsidian notes")

    for path in written:
        text = path.read_text(encoding="utf-8")
        check(text.startswith("---\n"), f"missing frontmatter: {path}")
        check("source: helpusai" in text, f"missing source: {path}")
        check("[[" in text or path.name != "Home.md", f"home should contain wikilinks: {path}")

    protocol = (exporter.DEFAULT_VAULT_DIR / "Watcher Protocol.md").read_text(encoding="utf-8")
    check("send-chat-message" in protocol, "protocol missing send-chat-message")
    check("run-command" in protocol, "protocol missing run-command")
    check("gateway-brain-supervisor" in protocol, "protocol missing gateway supervisor")

    lessons = (exporter.DEFAULT_VAULT_DIR / "Operational Lessons.md").read_text(encoding="utf-8")
    check("RECEBIDO_HELPUSAI_SUPERVISOR_009" in lessons, "lessons missing evidence marker")
    check("submit_not_confirmed_composer_still_has_text" in lessons, "lessons missing composer error")

    print("OK smoke_obsidian_vault")


if __name__ == "__main__":
    main()
