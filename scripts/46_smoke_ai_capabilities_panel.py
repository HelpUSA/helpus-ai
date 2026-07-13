
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
    "smoke:phase-v-ui": "python scripts/46_smoke_ai_capabilities_panel.py",
    "smoke:phase-v": "npm run smoke:phase-v-ui && npm run smoke:local-audit-safety",
}
for key, expected in expected_scripts.items():
    actual = scripts.get(key)
    assert actual == expected, f"unexpected package script {key}: {actual!r}"

for marker in [
    "Capacidades da IA",
    "Painel read-only",
    "Baseline Phase U",
    "smoke:phase-u",
    "smoke:local-audit-safety",
    "SMOKE_LOCAL_AUDIT_SAFETY_INDEX_OK",
    "SMOKE_LOCAL_EXECUTOR_ABSENT_OK",
    "Execucao local no app: bloqueada",
    "Aprovacao automatica no app: bloqueada",
    "Fetch automatico de detalhe: bloqueado",
    "Patch/commit via gateway ou shell explicito",
    "Uso pratico atual",
]:
    assert marker in page, f"missing AI capabilities panel marker: {marker}"

for marker in [
    "Detalhe da proposta",
    "proposal_id detectado automaticamente",
    "proposal_id normalizado para detalhe",
    "proposal_id codificado para endpoint de detalhe",
    "Status do proposal_id para detalhe",
    "Limite da consulta GET de detalhe",
]:
    assert marker in page, f"missing existing detail marker after Phase V: {marker}"

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
    "Phase V: AI capabilities status panel",
    "smoke:phase-v",
    "46_smoke_ai_capabilities_panel.py",
]:
    assert marker in doc, f"missing Phase V marker in capabilities doc: {marker}"

for marker in [
    "AI capabilities panel after Phase V",
    "smoke:phase-v",
]:
    assert marker in local_doc, f"missing Phase V marker in local audit doc: {marker}"

for marker in [
    "Checkpoint Phase V AI capabilities panel",
    "smoke:phase-v",
]:
    assert marker in status_doc, f"missing Phase V marker in status doc: {marker}"

for marker in [
    "Phase V AI capabilities status panel",
    "smoke:phase-v",
]:
    assert marker in roadmap, f"missing Phase V marker in roadmap: {marker}"

print("SMOKE_AI_CAPABILITIES_PANEL_OK")
