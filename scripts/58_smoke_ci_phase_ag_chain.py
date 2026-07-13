
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_57 = ROOT / "scripts/57_smoke_handoff_readiness_checklist.py"
SMOKE_56 = ROOT / "scripts/56_smoke_ci_phase_ae_chain.py"
SMOKE_55 = ROOT / "scripts/55_smoke_handoff_download.py"
SMOKE_54 = ROOT / "scripts/54_smoke_ci_phase_ac_chain.py"

for required in [
    WORKFLOW,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_57,
    SMOKE_56,
    SMOKE_55,
    SMOKE_54,
]:
    assert required.exists(), f"missing required file: {required}"

workflow = WORKFLOW.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

package = json.loads(
    PACKAGE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )
)

capabilities = CAPABILITIES.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

local_audit = LOCAL_AUDIT.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

status = STATUS.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

roadmap = ROADMAP.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

expected_scripts = {
    "smoke:phase-ah-ci":
        "python scripts/58_smoke_ci_phase_ag_chain.py",
    "smoke:phase-ah":
        "npm run smoke:phase-ah-ci && npm run smoke:phase-ag",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "name: Local audit safety",
    "permissions:",
    "contents: read",
    "Validate Phase AG CI contract",
    "python scripts/58_smoke_ci_phase_ag_chain.py",
    "Run complete handoff readiness smoke chain",
    "npm run smoke:phase-ag",
    "npm run smoke:phase-ae",
    "npm run smoke:phase-ac",
]:
    assert marker in workflow, (
        f"missing workflow marker: {marker}"
    )

for marker in [
    "smoke:phase-ag-ui",
    "smoke:phase-ag",
    "smoke:phase-af",
    "smoke:phase-ae",
    "smoke:phase-ad",
    "smoke:phase-ac",
    "smoke:phase-ab",
    "smoke:phase-aa",
    "smoke:phase-z",
    "smoke:local-audit-safety",
]:
    assert marker in package["scripts"], (
        f"missing smoke dependency: {marker}"
    )

for marker in [
    "Phase AH implementation contract",
    "smoke:phase-ah",
    "58_smoke_ci_phase_ag_chain.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Phase AG CI chain after Phase AH",
    "smoke:phase-ah",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AH CI Phase AG chain",
    "smoke:phase-ah",
]:
    assert marker in status, marker

for marker in [
    "Phase AH CI Phase AG chain",
    "smoke:phase-ah",
]:
    assert marker in roadmap, marker

print("SMOKE_CI_PHASE_AG_CHAIN_OK")
