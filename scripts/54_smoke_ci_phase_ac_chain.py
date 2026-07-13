
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_53 = ROOT / "scripts/53_smoke_handoff_copy_clipboard.py"
SMOKE_52 = ROOT / "scripts/52_smoke_handoff_summary_preview.py"
SMOKE_51 = ROOT / "scripts/51_smoke_ci_phase_z_chain.py"

for required in [
    WORKFLOW,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_53,
    SMOKE_52,
    SMOKE_51,
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
    "smoke:phase-ad-ci":
        "python scripts/54_smoke_ci_phase_ac_chain.py",
    "smoke:phase-ad":
        "npm run smoke:phase-ad-ci && npm run smoke:phase-ac",
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
    "Validate Phase AC CI contract",
    "python scripts/54_smoke_ci_phase_ac_chain.py",
    "Run complete handoff copy smoke chain",
    "npm run smoke:phase-ac",
    "npm run smoke:phase-z",
    "npm run smoke:phase-w",
]:
    assert marker in workflow, (
        f"missing workflow marker: {marker}"
    )

for marker in [
    "smoke:phase-ac-ui",
    "smoke:phase-ac",
    "smoke:phase-ab",
    "smoke:phase-aa",
    "smoke:phase-z",
    "smoke:local-audit-safety",
]:
    assert marker in package["scripts"], (
        f"missing previous smoke dependency: {marker}"
    )

for marker in [
    "Phase AD implementation contract",
    "smoke:phase-ad",
    "54_smoke_ci_phase_ac_chain.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Phase AC CI chain after Phase AD",
    "smoke:phase-ad",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AD CI Phase AC chain",
    "smoke:phase-ad",
]:
    assert marker in status, marker

for marker in [
    "Phase AD CI Phase AC chain",
    "smoke:phase-ad",
]:
    assert marker in roadmap, marker

print("SMOKE_CI_PHASE_AC_CHAIN_OK")
