import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPUSAI = ROOT / "scripts" / "helpusai"
sys.path.insert(0, str(HELPUSAI))

import export_obsidian_operational_lessons as exporter


def check(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    written = exporter.export_operational_lessons()
    names = {path.name for path in written}

    check("Operational Lessons.md" in names, "missing operational lessons index")
    check("AI Bridge Local Interchat.md" in names, "missing interchat lesson note")
    check("AI Bridge Local Envelope.md" in names, "missing envelope lesson note")
    check("AI Bridge Local Delivery.md" in names, "missing delivery lesson note")
    check("AI Bridge Local Run Command.md" in names, "missing run command lesson note")

    index = (exporter.DEFAULT_VAULT_DIR / "Operational Lessons.md").read_text(encoding="utf-8")
    check("[[Operational Lessons/AI Bridge Local Interchat|AI Bridge Local Interchat]]" in index, "index missing interchat wikilink")
    check("operational_lesson_index" in index, "index missing kind")

    interchat = (exporter.DEFAULT_LESSONS_DIR / "AI Bridge Local Interchat.md").read_text(encoding="utf-8")
    check("kind: operational_lesson" in interchat, "interchat missing kind")
    check("send-chat-message" in interchat, "interchat missing protocol correction")
    check("RECEBIDO_HELPUSAI_SUPERVISOR_009" in interchat, "interchat missing evidence")

    envelope = (exporter.DEFAULT_LESSONS_DIR / "AI Bridge Local Envelope.md").read_text(encoding="utf-8")
    check("envelope_parse_error" in envelope, "envelope lesson missing error marker")
    check("marcadores reais" in envelope.lower(), "envelope lesson missing marker guidance")

    delivery = (exporter.DEFAULT_LESSONS_DIR / "AI Bridge Local Delivery.md").read_text(encoding="utf-8")
    check("submit_not_confirmed_composer_still_has_text" in delivery, "delivery lesson missing composer error")

    run_command = (exporter.DEFAULT_LESSONS_DIR / "AI Bridge Local Run Command.md").read_text(encoding="utf-8")
    check("gateway-brain-supervisor" in run_command, "run command lesson missing gateway supervisor")
    check("local_capability" in run_command, "run command lesson missing local capability")

    print("OK smoke_obsidian_operational_lessons")


if __name__ == "__main__":
    main()
