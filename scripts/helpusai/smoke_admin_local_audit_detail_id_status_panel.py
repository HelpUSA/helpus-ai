from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
DOC = ROOT / "docs/local-plan-audit.md"

page = PAGE.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(PACKAGE.read_text(encoding="utf-8-sig", errors="replace"))
doc = DOC.read_text(encoding="utf-8-sig", errors="replace")

required = [
    "Status do proposal_id para detalhe",
    "proposalDetailId.trim()",
    "Pronto para consulta GET read-only.",
    "Informe ou preencha um proposal_id antes de carregar o detalhe.",
    "Preview GET detalhe auditavel",
    "Carregar detalhe auditavel",
]
for marker in required:
    assert marker in page, f"missing detail id status marker: {marker}"

start = page.index("Status do proposal_id para detalhe")
end = page.index("Preview GET detalhe auditavel", start)
status_block = page[start:end]
for forbidden in [
    "fetchLocal",
    "postLocal",
    "method: 'POST'",
    "setProposalDetailId",
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]:
    assert forbidden not in status_block, f"forbidden token in detail id status: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-n-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_id_status_panel.py"
assert scripts["smoke:phase-n"] == "npm run smoke:phase-n-ui && npm run smoke:phase-m"

for marker in [
    "Phase N",
    "Detail proposal_id status UI read-only",
    "Status do proposal_id para detalhe",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_id_status_panel")
