from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

WORKFLOW = ROOT / ".github/workflows/local-audit-safety.yml"
PACKAGE = ROOT / "package.json"

CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_69 = ROOT / "scripts/69_smoke_chat_markdown_rendering.py"
SMOKE_68 = ROOT / "scripts/68_smoke_ci_phase_aq_chain.py"
SMOKE_38 = ROOT / "scripts/38_smoke_local_executor_absent.py"
SMOKE_43 = ROOT / "scripts/43_smoke_local_detail_ui_safety_contract.py"

MAIN = ROOT / "backend/main.py"
AUDIT = ROOT / "backend/local_plan_audit.py"

for required in [
    WORKFLOW,
    PACKAGE,
    CAPABILITIES,
    STATUS,
    ROADMAP,
    SMOKE_69,
    SMOKE_68,
    SMOKE_38,
    SMOKE_43,
    MAIN,
    AUDIT,
]:
    assert required.exists(), (
        f"missing required file: {required}"
    )

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

status = STATUS.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

roadmap = ROADMAP.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

main = MAIN.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

audit = AUDIT.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

smoke_38 = SMOKE_38.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

smoke_43 = SMOKE_43.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

expected_scripts = {
    "smoke:phase-at-ci":
        "python scripts/70_smoke_ci_phase_as_chain.py",
    "smoke:phase-at":
        "npm run smoke:phase-at-ci && npm run smoke:phase-as",
    "smoke:phase-as":
        "npm run smoke:phase-as-ui && npm run smoke:phase-ar",
    "smoke:phase-ar":
        "npm run smoke:phase-ar-ci && npm run smoke:phase-aq",
    "smoke:phase-aq":
        "npm run smoke:phase-aq-ui && npm run smoke:phase-ap",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: "
        f"{actual!r}"
    )

workflow_markers = [
    "name: Local audit safety",
    "permissions:",
    "contents: read",
    "jobs:",
    "local-audit-safety:",
    "name: Local audit safety smoke chain",
    "runs-on: ubuntu-latest",
    "timeout-minutes: 15",
    "actions/checkout@v4",
    "actions/setup-node@v4",
    "node-version: '22'",
    "actions/setup-python@v5",
    "python-version: '3.12'",
    "if [ -f package-lock.json ]; then",
    "npm ci",
    "else",
    "npm install",
    "fi",
    "Validate Phase AQ central chat contract",
    "python scripts/68_smoke_ci_phase_aq_chain.py",
    "Run complete central chat smoke chain",
    "npm run smoke:phase-aq",
    "Validate Phase AS safe markdown contract",
    "python scripts/70_smoke_ci_phase_as_chain.py",
    "Run complete safe markdown chat smoke chain",
    "npm run smoke:phase-at",
]

for marker in workflow_markers:
    assert marker in workflow, (
        f"missing workflow marker: {marker}"
    )

position_aq = workflow.index(
    "Run complete central chat smoke chain"
)

position_at_validate = workflow.index(
    "Validate Phase AS safe markdown contract"
)

position_at_run = workflow.index(
    "Run complete safe markdown chat smoke chain"
)

assert position_aq < position_at_validate, (
    "Phase AT validation step must follow "
    "the Phase AQ workflow chain"
)

assert position_at_validate < position_at_run, (
    "Phase AT cumulative run must follow "
    "the Phase AT contract validation"
)

for marker in [
    "smoke:phase-at-ci",
    "smoke:phase-at",
    "smoke:phase-as-ui",
    "smoke:phase-as",
    "smoke:phase-ar-ci",
    "smoke:phase-ar",
    "smoke:phase-aq-ui",
    "smoke:phase-aq",
    "smoke:local-audit-safety",
]:
    assert marker in package["scripts"], (
        f"missing smoke dependency: {marker}"
    )

for marker in [
    "Phase AT CI validation contract",
    "scripts/70_smoke_ci_phase_as_chain.py",
    "smoke:phase-at-ci",
    "smoke:phase-at",
    "AT -> AS -> AR -> AQ",
    "contents: read",
]:
    assert marker in capabilities, marker

for marker in [
    "Checkpoint Phase AT CI Phase AS chain",
    "scripts/70_smoke_ci_phase_as_chain.py",
    "smoke:phase-at",
    "AT -> AS -> AR -> AQ",
]:
    assert marker in status, marker

for marker in [
    "Phase AT CI Phase AS chain",
    "scripts/70_smoke_ci_phase_as_chain.py",
    "smoke:phase-at",
    "AT -> AS -> AR -> AQ",
]:
    assert marker in roadmap, marker

for forbidden in [
    '@app.post("/local/execute"',
    '@app.post("/local/commands"',
    '@app.post("/local/plan/execute"',
    '@app.post("/local/plan/run"',
    '@app.post("/local/plan/approve"',
    '@app.patch("/local/plan/approve"',
]:
    assert forbidden not in main, (
        f"forbidden execution or approval endpoint: "
        f"{forbidden}"
    )

for forbidden in [
    "subprocess.",
    "os.system(",
    "Popen(",
    "check_call(",
    "check_output(",
    "approved = True",
    '"approved": True',
    "'approved': True",
    '"executed": True',
    "'executed': True",
]:
    assert forbidden not in audit, (
        f"forbidden local executor marker: "
        f"{forbidden}"
    )

for required in [
    'AUDIT_CONTRACT_VERSION = "local-plan-audit-v1"',
    '"mode": "proposal_only"',
    '"executed": False',
    '"approved": False',
    '"approval_status": "pending_human_review"',
    '"requires_human_confirmation": True',
]:
    assert required in audit, (
        f"missing local safety invariant: "
        f"{required}"
    )

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert forbidden not in workflow, (
        f"forbidden workflow marker: {forbidden}"
    )

for marker in [
    "SMOKE_LOCAL_EXECUTOR_ABSENT_OK",
    "forbidden_endpoint_markers",
    "forbidden_audit_markers",
    "required_audit_markers",
]:
    assert marker in smoke_38, (
        f"missing executor-absence smoke marker: "
        f"{marker}"
    )

for marker in [
    "SMOKE_LOCAL_DETAIL_UI_SAFETY_CONTRACT_OK",
    "positions =",
    "block = page[start:end]",
    "for token in forbidden",
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert marker in smoke_43, (
        f"missing contextual detail safety marker: "
        f"{marker}"
    )

print("SMOKE_CI_PHASE_AS_CHAIN_OK")
