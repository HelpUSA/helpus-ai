from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from helpus_operational_lesson_context import built_in_operational_lessons
from helpus_operational_lessons import OperationalLesson


DEFAULT_VAULT_DIR = Path("knowledge/obsidian/HelpUSAI")
DEFAULT_LESSONS_DIR = DEFAULT_VAULT_DIR / "Operational Lessons"


@dataclass(frozen=True)
class LessonNote:
    lesson: OperationalLesson
    filename: str
    title: str

    def render(self) -> str:
        created = datetime.now(timezone.utc).date().isoformat()
        tags = "\n".join(f"  - {tag}" for tag in ("helpusai", "operational_lesson", *self.lesson.tags))

        return (
            "---\n"
            f"title: {self.title}\n"
            "source: helpusai\n"
            "kind: operational_lesson\n"
            f"topic: {self.lesson.topic}\n"
            f"status: {self.lesson.status}\n"
            f"confidence: {self.lesson.confidence}\n"
            f"created: {created}\n"
            "tags:\n"
            f"{tags}\n"
            "---\n\n"
            f"# {self.title}\n\n"
            f"Status: `{self.lesson.status}`\n\n"
            f"Topic: `{self.lesson.topic}`\n\n"
            f"Confidence: `{self.lesson.confidence}`\n\n"
            "## Problema\n\n"
            f"{self.lesson.problem}\n\n"
            "## Correção\n\n"
            f"{self.lesson.correction}\n\n"
            "## Evidência\n\n"
            f"{self.lesson.evidence or 'Sem evidência registrada.'}\n\n"
            "## Links\n\n"
            "- [[Operational Lessons]]\n"
            "- [[AI Bridge Local]]\n"
            "- [[Watcher Protocol]]\n"
        )


def slug_to_title(topic: str) -> str:
    acronym_map = {
        "ai": "AI",
        "api": "API",
        "json": "JSON",
        "url": "URL",
        "id": "ID",
    }

    parts = re.split(r"[_:\-]+", topic.strip())
    title_parts: list[str] = []

    for part in parts:
        if not part:
            continue
        lowered = part.lower()
        title_parts.append(acronym_map.get(lowered, lowered.capitalize()))

    return " ".join(title_parts)


def safe_filename(title: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9 ._-]+", "", title).strip()
    clean = re.sub(r"\s+", " ", clean)
    return f"{clean or 'Operational Lesson'}.md"


def build_lesson_notes() -> list[LessonNote]:
    notes: list[LessonNote] = []
    seen: set[str] = set()

    for lesson in built_in_operational_lessons():
        title = slug_to_title(lesson.topic)
        filename = safe_filename(title)

        if filename in seen:
            suffix = len(seen) + 1
            filename = filename.replace(".md", f" {suffix}.md")

        seen.add(filename)
        notes.append(LessonNote(lesson=lesson, filename=filename, title=title))

    return notes


def render_lessons_index(notes: list[LessonNote]) -> str:
    created = datetime.now(timezone.utc).date().isoformat()
    lines = [
        "---",
        "title: Operational Lessons",
        "source: helpusai",
        "kind: operational_lesson_index",
        f"created: {created}",
        "tags:",
        "  - helpusai",
        "  - lessons",
        "  - operations",
        "---",
        "",
        "# Operational Lessons",
        "",
        "Este índice lista lessons operacionais exportadas para o Obsidian.",
        "",
        "## Lessons",
        "",
    ]

    for note in notes:
        lines.append(f"- [[Operational Lessons/{note.title}|{note.title}]] — `{note.lesson.status}`")

    lines.extend(
        [
            "",
            "## Fluxo recomendado",
            "",
            "1. HelpUSAI registra uma lesson candidata.",
            "2. A lesson é revisada no Obsidian.",
            "3. Lessons validadas podem virar regras promovidas.",
            "4. Rules promovidas entram no contexto operacional da HelpUSAI.",
            "",
            "## Links",
            "",
            "- [[Home]]",
            "- [[AI Bridge Local]]",
            "- [[Watcher Protocol]]",
            "- [[HelpUSAI Memory]]",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def export_operational_lessons(
    *,
    vault_dir: Path = DEFAULT_VAULT_DIR,
    lessons_dir: Path = DEFAULT_LESSONS_DIR,
) -> list[Path]:
    vault_dir.mkdir(parents=True, exist_ok=True)
    lessons_dir.mkdir(parents=True, exist_ok=True)

    notes = build_lesson_notes()
    written: list[Path] = []

    index_path = vault_dir / "Operational Lessons.md"
    index_path.write_text(render_lessons_index(notes), encoding="utf-8")
    written.append(index_path)

    for note in notes:
        path = lessons_dir / note.filename
        path.write_text(note.render().rstrip() + "\n", encoding="utf-8")
        written.append(path)

    return written


def main() -> None:
    written = export_operational_lessons()
    print("OBSIDIAN_OPERATIONAL_LESSONS_EXPORTED")
    for path in written:
        print(path.as_posix())


if __name__ == "__main__":
    main()
