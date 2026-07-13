
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_55 = ROOT / "scripts/55_smoke_handoff_download.py"
SMOKE_54 = ROOT / "scripts/54_smoke_ci_phase_ac_chain.py"
SMOKE_53 = ROOT / "scripts/53_smoke_handoff_copy_clipboard.py"
SMOKE_52 = ROOT / "scripts/52_smoke_handoff_summary_preview.py"

for required in [
    WORKFLOW,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_55,
    SMOKE_54,
    SMOKE_53,
    SMOKE_52,
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
    "smoke:phase-af-ci":
        "python scripts/56_smoke_ci_phase_ae_chain.py",
    "smoke:phase-af":
        "npm run smoke:phase-af-ci && npm run smoke:phase-ae",
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
    "Validate Phase AE CI contract",
    "python scripts/56_smoke_ci_phase_ae_chain.py",
    "Run complete handoff download smoke chain",
    "npm run smoke:phase-ae",
    "npm run smoke:phase-ac",
    "npm run smoke:phase-z",
]:
    assert marker in workflow, (
        f"missing workflow marker: {marker}"
    )

for marker in [
    "smoke:phase-ae-ui",
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
    "Phase AF implementation contract",
    "smoke:phase-af",
    "56_smoke_ci_phase_ae_chain.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Phase AE CI chain after Phase AF",
    "smoke:phase-af",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AF CI Phase AE chain",
    "smoke:phase-af",
]:
    assert marker in status, marker

for marker in [
    "Phase AF CI Phase AE chain",
    "smoke:phase-af",
]:
    assert marker in roadmap, marker

print("SMOKE_CI_PHASE_AE_CHAIN_OK")
