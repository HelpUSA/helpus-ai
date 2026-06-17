from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "HELPUSAI_MEMORY_STORAGE_OBSIDIAN_EXPORT_INSPECTION_2026-06-17.md"


def check(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    check(REPORT.exists(), "inspection report missing")

    text = REPORT.read_text(encoding="utf-8")

    required = [
        "MEMORY_STORAGE_OBSIDIAN_INSPECTION_OK",
        "operational_lesson",
        "safe_record_chat_memory_event",
        "Obsidian",
        "readonly",
        "Recomendação para o bloco 15B",
    ]

    for marker in required:
        check(marker in text, f"missing marker: {marker}")

    check("Nenhuma conexao externa foi aberta" in text, "report must state no external connection")
    check("helpus_operational_lessons.py" in text, "report missing operational lessons file")
    check("helpus_internal_memory_recorder.py" in text, "report missing memory recorder file")

    print("OK smoke_memory_storage_obsidian_inspection")


if __name__ == "__main__":
    main()
