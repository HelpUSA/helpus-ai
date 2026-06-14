from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DOCS = {
    "release": "docs/HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md",
    "backlog": "docs/HELPUS_POST_COMPLETION_BACKLOG.md",
    "runbook": "docs/HELPUS_WATCHER_OPERATIONS_RUNBOOK.md",
    "master": "docs/HELPUS_PROJECT_MASTER.md",
    "report": "reports/HELPUS_FINAL_REPORT_2026-06-14.md",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig", errors="replace")


def assert_contains(text: str, marker: str, label: str) -> None:
    if marker not in text:
        raise AssertionError("Missing {!r} in {}".format(marker, label))


def assert_not_contains(text: str, marker: str, label: str) -> None:
    if marker in text:
        raise AssertionError("Forbidden {!r} in {}".format(marker, label))


def main() -> None:
    missing = [path for path in DOCS.values() if not (ROOT / path).exists()]
    if missing:
        raise AssertionError("Missing release gate docs: " + repr(missing))

    release = read(DOCS["release"])
    for marker in [
        "This checklist is a decision gate, not a deploy command.",
        "Tag only after explicit human authorization.",
        "Deploy only after explicit human authorization.",
        "Never mix deploy with feature patches.",
        "No deploy, tag, reset hard, git clean, secrets or mass removal without explicit authorization.",
    ]:
        assert_contains(release, marker, DOCS["release"])

    backlog = read(DOCS["backlog"])
    for marker in [
        "This backlog is planning only",
        "No tag is created by this backlog.",
        "No deploy is executed by this backlog.",
        "Always prohibited without explicit authorization",
    ]:
        assert_contains(backlog, marker, DOCS["backlog"])

    runbook = read(DOCS["runbook"])
    for marker in [
        "This is an operations guide, not a deploy command.",
        "Forbidden without explicit authorization",
        "deploy",
        "tag or release creation",
        "printing or editing secrets",
    ]:
        assert_contains(runbook, marker, DOCS["runbook"])

    master = read(DOCS["master"])
    for marker in [
        "sem deploy",
        "analysis_only",
        "Release, tag and deploy",
        "Post completion backlog",
        "Active documentation index",
    ]:
        assert_contains(master, marker, DOCS["master"])

    report = read(DOCS["report"])
    for marker in [
        "Nenhum deploy executado",
        "Nenhum reset hard, git clean, tag ou remocao em massa executado.",
        "Autorizar ou nao tag/release formal",
        "Autorizar ou nao deploy",
    ]:
        assert_contains(report, marker, DOCS["report"])

    for path in DOCS.values():
        text = read(path).lower()
        assert_contains(text, "reset", path)
        assert_contains(text, "git clean", path)
        assert_contains(text, "deploy", path)

    print("RELEASE_DEPLOY_GATE_SMOKE_OK")


if __name__ == "__main__":
    main()

