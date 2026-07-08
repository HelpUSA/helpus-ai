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
    "proposal_id normalizado para detalhe",
    "proposalDetailId.trim() || 'Nenhum proposal_id informado.'",
    "Valor read-only: derivado do campo manual/de detalhe",
    "Status do proposal_id para detalhe",
    "Preview GET detalhe auditavel",
    "Carregar detalhe auditavel",
]
for marker in required:
    assert marker in page, f"missing normalized id marker: {marker}"

start = page.index("proposal_id normalizado para detalhe")
end = page.index("Preview GET detalhe auditavel", start)
normalized_block = page[start:end]
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
    assert forbidden not in normalized_block, f"forbidden token in normalized id block: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-o-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_normalized_id_panel.py"
assert scripts["smoke:phase-o"] == "npm run smoke:phase-o-ui && npm run smoke:phase-n"

for marker in [
    "Phase O",
    "Detail normalized proposal_id UI read-only",
    "proposal_id normalizado para detalhe",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_normalized_id_panel")
