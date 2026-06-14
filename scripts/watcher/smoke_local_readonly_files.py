from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.local_readonly_files import LocalReadonlyFiles

def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")

def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)

def main() -> None:
    reader = LocalReadonlyFiles(ROOT, max_bytes=80)

    ok_doc = reader.read_text("docs/HELPUS_PROJECT_MASTER.md")
    assert_true(ok_doc["ok"], "master doc must be readable")
    assert_equal(ok_doc["path"], "docs/HELPUS_PROJECT_MASTER.md", "normalized doc path")
    assert_true(ok_doc["size"] > 0, "master doc size")
    assert_equal(ok_doc["truncated"], True, "large doc is truncated")

    missing = reader.read_text("docs/NO_SUCH_FILE.md")
    assert_equal(missing["ok"], False, "missing file ok")
    assert_equal(missing["reason"], "not_found", "missing file reason")

    traversal = reader.read_text("../backend/.env")
    assert_equal(traversal["ok"], False, "traversal blocked")
    assert_equal(traversal["reason"], "path_traversal_blocked", "traversal reason")

    absolute = reader.read_text(str((ROOT  / "docs/HELPUS_PROJECT_MASTER.md").resolve()))
    assert_equal(absolute["ok"], False, "absolute path blocked")
    assert_equal(absolute["reason"], "absolute_path_blocked", "absolute reason")

    env_file = reader.read_text("backend/.env")
    assert_equal(env_file["ok"], False, "env blocked")
    assert_equal(env_file["reason"], "secret_path_blocked", "env reason")

    secret_marker = reader.read_text("docs/secret_notes.md")
    assert_equal(secret_marker["ok"], False, "secret marker blocked")
    assert_equal(secret_marker["reason"], "secret_marker_blocked", "secret marker reason")

    disallowed = reader.read_text("package.json")
    assert_equal(disallowed["ok"], False, "disallowed path blocked")
    assert_equal(disallowed["reason"], "path_not_allowed", "disallowed reason")

    report = reader.read_text("reports/HELPUS_FINAL_REPORT_2026-06-14.md")
    assert_true(report["ok"], "final report must be readable")

    print("LOCAL_READONLY_FILES_SMOKE_OK")

if __name__ == "__main__":
    main()
