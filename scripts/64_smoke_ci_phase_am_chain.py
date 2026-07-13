
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_63 = ROOT / "scripts/63_smoke_handoff_fingerprint_comparison.py"
SMOKE_62 = ROOT / "scripts/62_smoke_ci_phase_ak_chain.py"
SMOKE_61 = ROOT / "scripts/61_smoke_handoff_fingerprint.py"
SMOKE_60 = ROOT / "scripts/60_smoke_ci_phase_ai_chain.py"

for required in [
    WORKFLOW,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_63,
    SMOKE_62,
    SMOKE_61,
    SMOKE_60,
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
    "smoke:phase-an-ci":
        "python scripts/64_smoke_ci_phase_am_chain.py",
    "smoke:phase-an":
        "npm run smoke:phase-an-ci && npm run smoke:phase-am",
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
    "Validate Phase AM CI contract",
    "python scripts/64_smoke_ci_phase_am_chain.py",
    "Run complete fingerprint comparison smoke chain",
    "npm run smoke:phase-am",
    "npm run smoke:phase-ak",
    "npm run smoke:phase-ai",
]:
    assert marker in workflow, (
        f"missing workflow marker: {marker}"
    )

for marker in [
    "smoke:phase-am-ui",
    "smoke:phase-am",
    "smoke:phase-al",
    "smoke:phase-ak",
    "smoke:phase-aj",
    "smoke:phase-ai",
    "smoke:phase-ah",
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
    "Phase AN implementation contract",
    "smoke:phase-an",
    "64_smoke_ci_phase_am_chain.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Phase AM CI chain after Phase AN",
    "smoke:phase-an",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AN CI Phase AM chain",
    "smoke:phase-an",
]:
    assert marker in status, marker

for marker in [
    "Phase AN CI Phase AM chain",
    "smoke:phase-an",
]:
    assert marker in roadmap, marker

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert forbidden not in workflow, (
        f"forbidden workflow marker found: {forbidden}"
    )

print("SMOKE_CI_PHASE_AM_CHAIN_OK")
