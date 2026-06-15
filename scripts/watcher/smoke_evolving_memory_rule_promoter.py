from __future__ import annotations

from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from evolving_memory_lesson_extractor import LessonDraftExtractor
from evolving_memory_rule_promoter import RuleDraftPromoter, normalize_rule_name, priority_from_severity


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = (ROOT / "backend" / "evolving_memory_rule_promoter.py").read_text(encoding="utf-8")
    assert_true("subprocess" not in source, "rule promoter must not execute commands")
    assert_true("import requests" not in source, "rule promoter must not import requests")
    assert_true(normalize_rule_name("Generated Code Syntax Error!") == "generated-code-syntax-error", "rule name normalized")
    assert_true(priority_from_severity("high") == 80, "high severity priority")
    assert_true(priority_from_severity("medium") == 60, "medium severity priority")
    assert_true(priority_from_severity("low") == 40, "low severity priority")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "memory.sqlite"
        extractor = LessonDraftExtractor(db_path)
        promoter = RuleDraftPromoter(db_path)
        try:
            lesson = extractor.create_lesson_from_command_result(
                lesson_id="lesson-1",
                project_id="helpus-ai",
                command_result_id="result-1",
                return_code=1,
                stderr="SyntaxError: bad generated code",
                summary="generated code failed",
            )
            assert_true(lesson is not None, "lesson draft created")
            rule = promoter.promote_lesson_to_rule_draft(
                lesson_id="lesson-1",
                scope="helpus-ai",
                rule_id="rule-1",
            )
            assert_true(rule["id"] == "rule-1", "rule id persisted")
            assert_true(rule["scope"] == "helpus-ai", "rule scope persisted")
            assert_true(rule["status"] == "draft", "rule remains draft")
            assert_true(rule["enabled"] == 0, "rule is not enabled automatically")
            assert_true(rule["priority"] == 60, "priority from severity")
            assert_true(rule["name"] == "generated-code-syntax-error", "rule name from root cause")
            again = promoter.promote_lesson_to_rule_draft(lesson_id="lesson-1", scope="helpus-ai", rule_id="rule-duplicate")
            assert_true(again["id"] == "rule-1", "duplicate promotion returns existing rule")
            rules = promoter.list_rules(scope="helpus-ai", status="draft", limit=10)
            assert_true(len(rules) == 1, "list rules filters draft")
            try:
                promoter.list_rules(limit=0)
            except ValueError:
                pass
            else:
                raise AssertionError("invalid limit accepted")
        finally:
            promoter.close()
            extractor.close()

    print("EVOLVING_MEMORY_RULE_PROMOTER_SMOKE_OK")


if __name__ == "__main__":
    main()
