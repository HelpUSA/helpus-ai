from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    "docs/README.md",
    "docs/HELPUS_PROJECT_MASTER.md",
    "docs/HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md",
    "docs/HELPUS_WATCHER_OPERATIONS_RUNBOOK.md",
    "docs/HELPUS_POST_COMPLETION_BACKLOG.md",
    "reports/HELPUS_FINAL_REPORT_2026-06-14.md",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig", errors="replace")


def assert_contains(text: str, marker: str, label: str) -> None:
    if marker not in text:
        raise AssertionError("Missing {!r} in {}".format(marker, label))


def main() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        raise AssertionError("Missing active docs: " + repr(missing))

    readme = read("docs/README.md")
    for marker in [
        "HELPUS_PROJECT_MASTER.md",
        "HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md",
        "HELPUS_WATCHER_OPERATIONS_RUNBOOK.md",
        "HELPUS_POST_COMPLETION_BACKLOG.md",
        "HELPUS_FINAL_REPORT_2026-06-14.md",
    ]:
        assert_contains(readme, marker, "docs/README.md")

    master = read("docs/HELPUS_PROJECT_MASTER.md")
    for marker in [
        "Fechamento final 2026-06-14",
        "Active documentation index",
        "Micros 24 a 29 concluidos",
        "analysis_only",
    ]:
        assert_contains(master, marker, "docs/HELPUS_PROJECT_MASTER.md")

    release = read("docs/HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md")
    for marker in [
        "Release and deploy checklist",
        "Tag only after explicit human authorization",
        "Deploy only after explicit human authorization",
    ]:
        assert_contains(release, marker, "docs/HELPUS_RELEASE_AND_DEPLOY_CHECKLIST.md")

    runbook = read("docs/HELPUS_WATCHER_OPERATIONS_RUNBOOK.md")
    for marker in [
        "Standard work loop",
        "Receipt handling",
        "envelope_parse_error",
        "Forbidden without explicit authorization",
    ]:
        assert_contains(runbook, marker, "docs/HELPUS_WATCHER_OPERATIONS_RUNBOOK.md")

    backlog = read("docs/HELPUS_POST_COMPLETION_BACKLOG.md")
    for marker in [
        "Completed baseline",
        "Priority 1 - Release readiness without deploy",
        "Always prohibited without explicit authorization",
    ]:
        assert_contains(backlog, marker, "docs/HELPUS_POST_COMPLETION_BACKLOG.md")

    report = read("reports/HELPUS_FINAL_REPORT_2026-06-14.md")
    for marker in [
        "Relatorio final de conclusao",
        "Micro 29",
        "Nenhum deploy executado",
    ]:
        assert_contains(report, marker, "reports/HELPUS_FINAL_REPORT_2026-06-14.md")

    print("DOCS_INDEX_SMOKE_OK")


if __name__ == "__main__":
    main()
