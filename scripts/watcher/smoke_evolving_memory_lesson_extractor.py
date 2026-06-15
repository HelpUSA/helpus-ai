from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from evolving_memory_lesson_extractor import LessonDraftExtractor, classify_failure


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = (ROOT / "backend" / "evolving_memory_lesson_extractor.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "lesson extractor must not execute commands")
    assert_true("import requests" not in source, "lesson extractor must not import requests")

    parsed = classify_failure(return_code=1, stderr="Bad escaped character in JSON")
    assert_true(parsed["root_cause"] == "invalid_or_fragile_command_envelope", "json parse classified")
    syntax = classify_failure(return_code=1, stderr="IndentationError: expected an indented block")
    assert_true(syntax["root_cause"] == "generated_code_syntax_error", "syntax error classified")
    success = classify_failure(return_code=0, stderr="")
    assert_true(success["root_cause"] == "no_failure_detected", "success classified")

    with tempfile.TemporaryDirectory() as tmp:
        extractor = LessonDraftExtractor(Path(tmp) / "memory.sqlite")
        try:
            lesson = extractor.create_lesson_from_command_result(
                lesson_id="lesson-1",
                project_id="helpus-ai",
                command_result_id="result-1",
                return_code=1,
                stderr="SyntaxError: token=supersecret",
                summary="generated code failed",
            )
            assert_true(lesson is not None, "lesson created for failure")
            assert_true(lesson["id"] == "lesson-1", "lesson id persisted")
            assert_true(lesson["status"] == "draft", "lesson is draft")
            assert_true(lesson["severity"] == "medium", "severity classified")
            assert_true("supersecret" not in lesson["problem"], "problem sanitized")
            assert_true(extractor.create_lesson_from_command_result(project_id="helpus-ai", command_result_id="ok-1", return_code=0) is None, "success creates no lesson")
            lessons = extractor.list_lessons(project_id="helpus-ai", status="draft", limit=10)
            assert_true(len(lessons) == 1, "list lessons filters draft")
            try:
                extractor.list_lessons(limit=0)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid limit accepted")
        finally:
            extractor.close()

    print("EVOLVING_MEMORY_LESSON_EXTRACTOR_SMOKE_OK")


if __name__ == "__main__":
    main()
