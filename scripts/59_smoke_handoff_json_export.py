
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
HANDOFF = ROOT / "docs/ai/MULTI_AGENT_HANDOFF.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_58 = ROOT / "scripts/58_smoke_ci_phase_ag_chain.py"
SMOKE_57 = ROOT / "scripts/57_smoke_handoff_readiness_checklist.py"
SMOKE_56 = ROOT / "scripts/56_smoke_ci_phase_ae_chain.py"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    HANDOFF,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_58,
    SMOKE_57,
    SMOKE_56,
]:
    assert required.exists(), f"missing required file: {required}"

page = PAGE.read_text(
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

handoff = HANDOFF.read_text(
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
    "smoke:phase-ai-ui":
        "python scripts/59_smoke_handoff_json_export.py",
    "smoke:phase-ai":
        "npm run smoke:phase-ai-ui && npm run smoke:phase-ah",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "HandoffJsonExport",
    "buildHandoffJsonExport",
    "handoffJsonExport",
    "schemaVersion: 'helpusai.handoff.v1'",
    "generatedFrom: 'admin-local-read-only-preview'",
    "humanReviewRequired: true",
    "approved: false",
    "executed: false",
    "handoffJsonDownloadStatus",
    "setHandoffJsonDownloadStatus",
    "baixarResumoHandoffJson",
    "JSON.stringify(",
    "application/json;charset=utf-8",
    "link.download = 'helpusai-handoff.json'",
    "link.dispatchEvent(new MouseEvent('click'))",
    "Baixar .json",
    "onClick={baixarResumoHandoffJson}",
    "Arquivo JSON de handoff preparado localmente.",
    "Download JSON indisponivel.",
    "Preview JSON auditavel",
    "prettyJson(handoffJsonExport)",
    "humanReviewRequired=true",
    "approved=false",
    "executed=false",
    "smoke:phase-ai",
    "smoke:phase-ah",
]:
    assert marker in page, (
        f"missing Phase AI page marker: {marker}"
    )

for marker in [
    "Checklist de prontidao do handoff",
    "Baixar .txt",
    "Copiar handoff",
    "Resumo de handoff multiagente",
    "Modo de proposta de patch",
    "Matriz de risco estruturado",
    "Capacidades da IA",
]:
    assert marker in page, (
        f"missing previous UI marker: {marker}"
    )

for marker in [
    "Phase AI implementation contract",
    "smoke:phase-ai",
    "59_smoke_handoff_json_export.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Machine-readable JSON export after Phase AI",
    "smoke:phase-ai",
]:
    assert marker in handoff, marker

for marker in [
    "Handoff JSON export after Phase AI",
    "smoke:phase-ai",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AI handoff JSON export",
    "smoke:phase-ai",
]:
    assert marker in status, marker

for marker in [
    "Phase AI handoff JSON export",
    "smoke:phase-ai",
]:
    assert marker in roadmap, marker

assert page.count(
    "onClick={baixarResumoHandoffJson}"
) == 1, "JSON download must require one explicit click"

assert page.count(
    "link.download = 'helpusai-handoff.json'"
) == 1, "JSON filename must exist exactly once"

assert page.count(
    "approved: false"
) == 1, "approved false must exist exactly once"

assert page.count(
    "executed: false"
) == 1, "executed false must exist exactly once"

assert "approved: true" not in page
assert "executed: true" not in page
assert '"approved": true' not in page
assert '"executed": true' not in page

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert forbidden not in page, (
        f"forbidden execution marker found: {forbidden}"
    )

print("SMOKE_HANDOFF_JSON_EXPORT_OK")
