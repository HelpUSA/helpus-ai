
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"
DOC = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_DOC = ROOT / "docs/local-plan-audit.md"
STATUS_DOC = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"
SMOKE_47 = ROOT / "scripts/47_smoke_structured_proposal_risk_panel.py"
SMOKE_46 = ROOT / "scripts/46_smoke_ai_capabilities_panel.py"
SMOKE_45 = ROOT / "scripts/45_smoke_local_audit_safety_index.py"

for required in [WORKFLOW, PACKAGE, DOC, LOCAL_DOC, STATUS_DOC, ROADMAP, SMOKE_47, SMOKE_46, SMOKE_45]:
    assert required.exists(), f"missing required file: {required}"

workflow = WORKFLOW.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(PACKAGE.read_text(encoding="utf-8-sig", errors="replace"))
doc = DOC.read_text(encoding="utf-8-sig", errors="replace")
local_doc = LOCAL_DOC.read_text(encoding="utf-8-sig", errors="replace")
status_doc = STATUS_DOC.read_text(encoding="utf-8-sig", errors="replace")
roadmap = ROADMAP.read_text(encoding="utf-8-sig", errors="replace")

scripts = package["scripts"]
expected_scripts = {
    "smoke:phase-x-ci": "python scripts/48_smoke_ci_safety_workflow.py",
    "smoke:phase-x": "npm run smoke:phase-x-ci && npm run smoke:phase-w",
}
for key, expected in expected_scripts.items():
    actual = scripts.get(key)
    assert actual == expected, f"unexpected package script {key}: {actual!r}"

for marker in [
    "name: Local audit safety",
    "pull_request:",
    "branches:",
    "- main",
    "permissions:",
    "contents: read",
    "runs-on: ubuntu-latest",
    "timeout-minutes: 15",
    "actions/checkout@v4",
    "actions/setup-node@v4",
    "node-version: '22'",
    "actions/setup-python@v5",
    "python-version: '3.12'",
    "npm ci",
    "npm install",
    "python scripts/48_smoke_ci_safety_workflow.py",
    "npm run smoke:phase-w",
]:
    assert marker in workflow, f"missing workflow marker: {marker}"

for marker in [
    "smoke:phase-w-ui",
    "smoke:phase-w",
    "smoke:phase-v",
    "smoke:local-audit-safety",
]:
    assert marker in scripts, f"missing package smoke dependency: {marker}"

for marker in [
    "Phase X: CI safety workflow",
    "smoke:phase-x",
    "48_smoke_ci_safety_workflow.py",
    ".github/workflows/local-audit-safety.yml",
]:
    assert marker in doc, f"missing Phase X marker in capabilities doc: {marker}"

for marker in [
    "CI safety workflow after Phase X",
    "smoke:phase-x",
]:
    assert marker in local_doc, f"missing Phase X marker in local audit doc: {marker}"

for marker in [
    "Checkpoint Phase X CI safety workflow",
    "smoke:phase-x",
]:
    assert marker in status_doc, f"missing Phase X marker in status doc: {marker}"

for marker in [
    "Phase X CI safety workflow",
    "smoke:phase-x",
]:
    assert marker in roadmap, f"missing Phase X marker in roadmap: {marker}"

print("SMOKE_CI_SAFETY_WORKFLOW_OK")
