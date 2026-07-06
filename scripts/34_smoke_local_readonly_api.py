from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.local_readonly_files import LocalReadonlyFiles
from backend.local_repo_status import LocalRepoStatus


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    reader = LocalReadonlyFiles(ROOT, max_bytes=4096)

    allowed = reader.read_text("docs/HELPUS_PROJECT_MASTER.md")
    assert_true(allowed["ok"] is True, f"expected docs read to be allowed: {allowed}")
    assert_true(allowed["path"] == "docs/HELPUS_PROJECT_MASTER.md", allowed["path"])
    assert_true("HelpUS AI" in allowed["content"], "expected project master content")

    denied_env = reader.read_text("backend/.env")
    assert_true(denied_env["ok"] is False, f"expected backend/.env to be denied: {denied_env}")
    assert_true(denied_env["reason"] == "secret_path_blocked", denied_env["reason"])

    denied_traversal = reader.read_text("../outside.txt")
    assert_true(denied_traversal["ok"] is False, f"expected traversal to be denied: {denied_traversal}")
    assert_true(denied_traversal["reason"] == "path_traversal_blocked", denied_traversal["reason"])

    denied_root = reader.read_text("package.json")
    assert_true(denied_root["ok"] is False, f"expected package.json to be denied by prefix: {denied_root}")
    assert_true(denied_root["reason"] == "path_not_allowed", denied_root["reason"])

    denied_secret_marker = reader.read_text("docs/api_key_notes.md")
    assert_true(denied_secret_marker["ok"] is False, f"expected api_key marker to be denied: {denied_secret_marker}")
    assert_true(denied_secret_marker["reason"] == "secret_marker_blocked", denied_secret_marker["reason"])

    listed = reader.list_files("docs/", limit=20)
    assert_true(listed["ok"] is True, f"expected docs listing to be allowed: {listed}")
    listed_paths = {item["path"] for item in listed["files"]}
    assert_true("docs/HELPUS_PROJECT_MASTER.md" in listed_paths, f"expected project master in list: {listed_paths}")

    denied_list_root = reader.list_files(".")
    assert_true(denied_list_root["ok"] is False, f"expected root listing to be denied: {denied_list_root}")
    assert_true(denied_list_root["reason"] == "path_not_allowed", denied_list_root["reason"])

    denied_list_secret = reader.list_files("docs/api_key_notes")
    assert_true(denied_list_secret["ok"] is False, f"expected secret marker list to be denied: {denied_list_secret}")
    assert_true(denied_list_secret["reason"] == "secret_marker_blocked", denied_list_secret["reason"])

    search = reader.search_text("HelpUS AI", "docs/", limit=10)
    assert_true(search["ok"] is True, f"expected docs search to be allowed: {search}")
    assert_true(any(match["path"] == "docs/HELPUS_PROJECT_MASTER.md" for match in search["matches"]), f"expected project master match: {search}")

    denied_search = reader.search_text("HelpUS AI", "../outside", limit=10)
    assert_true(denied_search["ok"] is False, f"expected traversal search to be denied: {denied_search}")
    assert_true(denied_search["reason"] == "path_traversal_blocked", denied_search["reason"])

    short_search = reader.search_text("H", "docs/", limit=10)
    assert_true(short_search["ok"] is False, f"expected short query to be denied: {short_search}")
    assert_true(short_search["reason"] == "query_too_short", short_search["reason"])

    repo = LocalRepoStatus(ROOT, timeout_seconds=10)
    status = repo.status()
    assert_true(isinstance(status["ok"], bool), f"status ok should be boolean: {status}")
    assert_true("branch" in status and "head" in status and "dirty_files" in status, f"missing status keys: {status}")

    diff = repo.diff()
    assert_true(isinstance(diff["ok"], bool), f"diff ok should be boolean: {diff}")
    assert_true("check_return_code" in diff, f"missing diff check_return_code: {diff}")

    print("SMOKE_LOCAL_READONLY_API_OK")


if __name__ == "__main__":
    main()

