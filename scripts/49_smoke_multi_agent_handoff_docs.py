from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

HANDOFF = ROOT / "docs/ai/MULTI_AGENT_HANDOFF.md"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

required_files = [
    HANDOFF,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
]

for required in required_files:
    assert required.exists(), f"missing required file: {required}"

handoff = HANDOFF.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(
    PACKAGE.read_text(encoding="utf-8-sig", errors="replace")
)
capabilities = CAPABILITIES.read_text(
    encoding="utf-8-sig",
    errors="replace",
)
local_audit = LOCAL_AUDIT.read_text(
    encoding="utf-8-sig",
    errors="replace",
)
status = STATUS.read_text(encoding="utf-8-sig", errors="replace")
roadmap = ROADMAP.read_text(encoding="utf-8-sig", errors="replace")

expected_scripts = {
    "smoke:phase-y-handoff":
        "python scripts/49_smoke_multi_agent_handoff_docs.py",
    "smoke:phase-y":
        "npm run smoke:phase-y-handoff && npm run smoke:phase-x",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)
    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "Multi-agent handoff protocol",
    "Required handoff fields",
    "Successful handoff template",
    "Failed handoff template",
    "Shell cadence",
    "Gateway and watcher cadence",
    "Safety checklist",
    "HANDOFF_START",
    "HANDOFF_FAILURE_START",
    "base_commit",
    "final_commit",
    "changed_files",
    "validation",
    "next_action",
    "rollback",
    "Phase Y: multi-agent handoff docs",
    "Phase Z patch proposal mode",
]:
    assert marker in handoff, f"missing handoff marker: {marker}"

for marker in [
    "Phase Y: multi-agent handoff docs",
    "smoke:phase-y",
    "49_smoke_multi_agent_handoff_docs.py",
    "docs/ai/MULTI_AGENT_HANDOFF.md",
]:
    assert marker in capabilities, (
        f"missing capabilities marker: {marker}"
    )

for marker in [
    "Multi-agent handoff docs after Phase Y",
    "smoke:phase-y",
]:
    assert marker in local_audit, (
        f"missing local audit marker: {marker}"
    )

for marker in [
    "Checkpoint Phase Y multi-agent handoff docs",
    "smoke:phase-y",
]:
    assert marker in status, f"missing status marker: {marker}"

for marker in [
    "Phase Y multi-agent handoff docs",
    "smoke:phase-y",
]:
    assert marker in roadmap, f"missing roadmap marker: {marker}"

print("SMOKE_MULTI_AGENT_HANDOFF_DOCS_OK")
