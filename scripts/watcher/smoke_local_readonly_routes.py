from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "backend" / "main.py"


def assert_contains(text: str, marker: str, message: str) -> None:
    if marker not in text:
        raise AssertionError(f"{message}: missing {marker!r}")


def assert_route_is_admin_guarded(text: str, route: str, function_name: str) -> None:
    route_marker = f'@app.get("{route}")'
    fn_marker = f"async def {function_name}("
    route_pos = text.find(route_marker)
    fn_pos = text.find(fn_marker, route_pos)
    if route_pos < 0 or fn_pos < 0:
        raise AssertionError(f"missing route {route}")
    window = text[fn_pos : fn_pos + 260]
    if "Depends(obter_admin_google)" not in window:
        raise AssertionError(f"route {route} must require admin auth")


def main() -> None:
    text = MAIN.read_text(encoding="utf-8-sig")

    assert_contains(text, "from local_readonly_files import LocalReadonlyFiles", "readonly file helper import")
    assert_contains(text, "from local_repo_status import LocalRepoStatus", "repo status helper import")
    assert_contains(text, "LOCAL_REPO_ROOT = Path(__file__).resolve().parents[1]", "local repo root")
    assert_contains(text, "local_readonly_files = LocalReadonlyFiles(LOCAL_REPO_ROOT)", "readonly file instance")
    assert_contains(text, "local_repo_status = LocalRepoStatus(LOCAL_REPO_ROOT)", "repo status instance")

    assert_route_is_admin_guarded(text, "/local/status", "local_status")
    assert_route_is_admin_guarded(text, "/local/diff", "local_diff")
    assert_route_is_admin_guarded(text, "/local/files/read", "local_files_read")

    assert_contains(text, "return local_repo_status.status()", "status endpoint returns helper")
    assert_contains(text, "return local_repo_status.diff()", "diff endpoint returns helper")
    assert_contains(text, "return local_readonly_files.read_text(path)", "file endpoint returns helper")

    print("LOCAL_READONLY_ROUTES_SMOKE_OK")


if __name__ == "__main__":
    main()
