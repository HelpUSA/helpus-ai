
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
DOC = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_DOC = ROOT / "docs/local-plan-audit.md"
STATUS_DOC = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

for required in [PAGE, PACKAGE, DOC, LOCAL_DOC, STATUS_DOC, ROADMAP]:
    assert required.exists(), f"missing required file: {required}"

page = PAGE.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(PACKAGE.read_text(encoding="utf-8-sig", errors="replace"))
doc = DOC.read_text(encoding="utf-8-sig", errors="replace")
local_doc = LOCAL_DOC.read_text(encoding="utf-8-sig", errors="replace")
status_doc = STATUS_DOC.read_text(encoding="utf-8-sig", errors="replace")
roadmap = ROADMAP.read_text(encoding="utf-8-sig", errors="replace")

scripts = package["scripts"]
expected_scripts = {
    "smoke:phase-w-ui": "python scripts/47_smoke_structured_proposal_risk_panel.py",
    "smoke:phase-w": "npm run smoke:phase-w-ui && npm run smoke:phase-v",
}
for key, expected in expected_scripts.items():
    actual = scripts.get(key)
    assert actual == expected, f"unexpected package script {key}: {actual!r}"

for marker in [
    "summarizeStructuredProposalRisk",
    "structuredProposalRisk",
    "Matriz de risco estruturado",
    "Nivel de risco",
    "Smokes obrigatorios",
    "Rollback sugerido",
    "Justificativa do risco",
    "smoke:phase-w",
    "smoke:local-audit-safety",
    "Nao aprova, nao executa e nao chama API automaticamente",
]:
    assert marker in page, f"missing structured risk panel marker: {marker}"

for marker in [
    "Capacidades da IA",
    "smoke:phase-v",
    "SMOKE_LOCAL_AUDIT_SAFETY_INDEX_OK",
    "SMOKE_LOCAL_EXECUTOR_ABSENT_OK",
]:
    assert marker in page, f"missing Phase V marker after Phase W: {marker}"

for marker in [
    "Detalhe da proposta",
    "proposal_id detectado automaticamente",
    "proposal_id normalizado para detalhe",
    "proposal_id codificado para endpoint de detalhe",
]:
    assert marker in page, f"missing existing proposal detail marker after Phase W: {marker}"

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
    '"approved": True',
    "'approved': True",
    "approved = True",
    '"executed": True',
    "'executed': True",
    "executed = True",
]:
    assert forbidden not in page, f"forbidden token in admin local page: {forbidden}"

for marker in [
    "Phase W: structured proposal risk scoring",
    "smoke:phase-w",
    "47_smoke_structured_proposal_risk_panel.py",
]:
    assert marker in doc, f"missing Phase W marker in capabilities doc: {marker}"

for marker in [
    "Structured proposal risk scoring after Phase W",
    "smoke:phase-w",
]:
    assert marker in local_doc, f"missing Phase W marker in local audit doc: {marker}"

for marker in [
    "Checkpoint Phase W structured proposal risk scoring",
    "smoke:phase-w",
]:
    assert marker in status_doc, f"missing Phase W marker in status doc: {marker}"

for marker in [
    "Phase W structured proposal risk scoring",
    "smoke:phase-w",
]:
    assert marker in roadmap, f"missing Phase W marker in roadmap: {marker}"

print("SMOKE_STRUCTURED_PROPOSAL_RISK_PANEL_OK")
