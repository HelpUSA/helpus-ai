from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

PACKAGE = ROOT / "package.json"
PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
DOC = ROOT / "docs/local-plan-audit.md"
STATUS_DOC = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_38 = ROOT / "scripts/38_smoke_local_executor_absent.py"
SMOKE_43 = ROOT / "scripts/43_smoke_local_detail_ui_safety_contract.py"
SMOKE_44 = ROOT / "scripts/44_smoke_local_detail_safety_alias.py"

for required in [PACKAGE, PAGE, DOC, STATUS_DOC, ROADMAP, SMOKE_38, SMOKE_43, SMOKE_44]:
    assert required.exists(), f"missing required file: {required}"

package = json.loads(PACKAGE.read_text(encoding="utf-8-sig", errors="replace"))
page = PAGE.read_text(encoding="utf-8-sig", errors="replace")
doc = DOC.read_text(encoding="utf-8-sig", errors="replace")
status_doc = STATUS_DOC.read_text(encoding="utf-8-sig", errors="replace")
roadmap = ROADMAP.read_text(encoding="utf-8-sig", errors="replace")
smoke38 = SMOKE_38.read_text(encoding="utf-8-sig", errors="replace")
smoke43 = SMOKE_43.read_text(encoding="utf-8-sig", errors="replace")
smoke44 = SMOKE_44.read_text(encoding="utf-8-sig", errors="replace")

scripts = package["scripts"]
expected_scripts = {
    "smoke:local-detail-safety": "npm run smoke:phase-s-detail-safety && python scripts/38_smoke_local_executor_absent.py",
    "smoke:phase-t-alias": "python scripts/44_smoke_local_detail_safety_alias.py",
    "smoke:phase-t": "npm run smoke:phase-t-alias && npm run smoke:local-detail-safety && npm run smoke:phase-s",
    "smoke:local-audit-safety": "npm run smoke:local-detail-safety && python scripts/45_smoke_local_audit_safety_index.py",
    "smoke:phase-u-index": "python scripts/45_smoke_local_audit_safety_index.py",
    "smoke:phase-u": "npm run smoke:phase-u-index && npm run smoke:local-audit-safety && npm run smoke:phase-t",
}
for key, expected in expected_scripts.items():
    actual = scripts.get(key)
    assert actual == expected, f"unexpected package script {key}: {actual!r}"

for marker in ["SMOKE_LOCAL_DETAIL_SAFETY_ALIAS_OK", "AGGREGATE", "EXECUTOR_GUARD"]:
    assert marker in smoke44, f"missing Phase T alias smoke marker: {marker}"

for marker in ["SMOKE_LOCAL_DETAIL_UI_SAFETY_CONTRACT_OK", "postLocal", "setProposalDetailId"]:
    assert marker in smoke43, f"missing aggregate detail safety marker: {marker}"

assert "SMOKE_LOCAL_EXECUTOR_ABSENT_OK" in smoke38, "missing executor absence marker"

for marker in [
    "Detalhe da proposta",
    "Carregar detalhe auditavel",
    "GET /local/plan/proposals/{proposal_id}",
    "proposal_id detectado automaticamente",
    "proposal_id normalizado para detalhe",
    "proposal_id codificado para endpoint de detalhe",
    "Status do proposal_id para detalhe",
    "Checklist GET detalhe auditavel",
    "Limite da consulta GET de detalhe",
    "Contrato GET detalhe auditavel",
]:
    assert marker in page, f"missing read-only detail UI marker: {marker}"

for marker in [
    "Phase T: Detail safety smoke alias",
    "Phase U: Local audit safety index",
    "smoke:local-detail-safety",
    "smoke:local-audit-safety",
    "45_smoke_local_audit_safety_index.py",
]:
    assert marker in doc, f"missing audit doc marker: {marker}"

for marker in [
    "Checkpoint Phase T Detail safety smoke alias",
    "Checkpoint Phase U Local audit safety index",
    "smoke:phase-u",
    "smoke:local-audit-safety",
]:
    assert marker in status_doc, f"missing status marker: {marker}"

for marker in [
    "Phase T Detail safety smoke alias",
    "Phase U Local audit safety index",
    "smoke:phase-u",
    "smoke:local-audit-safety",
]:
    assert marker in roadmap, f"missing roadmap marker: {marker}"

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

print("SMOKE_LOCAL_AUDIT_SAFETY_INDEX_OK")
