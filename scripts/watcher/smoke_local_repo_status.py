from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.local_repo_status import LocalRepoStatus


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def assert_equal(actual, expected, message):
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def main() -> None:
    repo = LocalRepoStatus(ROOT)

    status = repo.status()
    assert_true(status["ok"], "repo status must be ok")
    assert_equal(status["branch"], "main", "branch")
    assert_true(len(status["head"]) >= 7, "head short hash")
    assert_true(isinstance(status["dirty_files"], list), "dirty files list")
    assert_true("## main" in status["status"], "status -sb includes branch")

    diff = repo.diff()
    assert_true(isinstance(diff["stat"], str), "diff stat text")
    assert_true("check_return_code" in diff, "diff check return code present")
    assert_true(isinstance(diff["check_stdout"], str), "diff check stdout text")
    assert_true(isinstance(diff["check_stderr"], str), "diff check stderr text")

    print("LOCAL_REPO_STATUS_SMOKE_OK")


if __name__ == "__main__":
    main()