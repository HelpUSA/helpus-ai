
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"
PHASE_Z_SMOKE = ROOT / "scripts/50_smoke_patch_proposal_mode.py"
PHASE_Y_SMOKE = ROOT / "scripts/49_smoke_multi_agent_handoff_docs.py"
PHASE_X_SMOKE = ROOT / "scripts/48_smoke_ci_safety_workflow.py"

for required in [
    WORKFLOW,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    PHASE_Z_SMOKE,
    PHASE_Y_SMOKE,
    PHASE_X_SMOKE,
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
    "smoke:phase-aa-ci":
        "python scripts/51_smoke_ci_phase_z_chain.py",
    "smoke:phase-aa":
        "npm run smoke:phase-aa-ci && npm run smoke:phase-z",
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
    "runs-on: ubuntu-latest",
    "Validate Phase Z CI contract",
    "python scripts/51_smoke_ci_phase_z_chain.py",
    "Run complete patch proposal smoke chain",
    "npm run smoke:phase-z",
    "npm run smoke:phase-w",
]:
    assert marker in workflow, (
        f"missing Phase AA workflow marker: {marker}"
    )

for marker in [
    "smoke:phase-z-ui",
    "smoke:phase-z",
    "smoke:phase-y",
    "smoke:phase-x",
    "smoke:phase-w",
    "smoke:local-audit-safety",
]:
    assert marker in package["scripts"], (
        f"missing smoke dependency: {marker}"
    )

for marker in [
    "Phase AA implementation contract",
    "smoke:phase-aa",
    "51_smoke_ci_phase_z_chain.py",
    ".github/workflows/local-audit-safety.yml",
]:
    assert marker in capabilities, (
        f"missing capabilities marker: {marker}"
    )

for marker in [
    "Phase Z CI chain after Phase AA",
    "smoke:phase-aa",
]:
    assert marker in local_audit, (
        f"missing local audit marker: {marker}"
    )

for marker in [
    "Checkpoint Phase AA CI Phase Z chain",
    "smoke:phase-aa",
]:
    assert marker in status, (
        f"missing status marker: {marker}"
    )

for marker in [
    "Phase AA CI Phase Z chain",
    "smoke:phase-aa",
]:
    assert marker in roadmap, (
        f"missing roadmap marker: {marker}"
    )

print("SMOKE_CI_PHASE_Z_CHAIN_OK")
