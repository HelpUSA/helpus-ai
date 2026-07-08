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
    "proposal_id codificado para endpoint de detalhe",
    "proposalDetailId.trim()",
    "encodeURIComponent(proposalDetailId.trim())",
    "Nenhum proposal_id para codificar.",
    "Valor read-only: apenas mostra a codificacao",
    "Preview GET detalhe auditavel",
    "Carregar detalhe auditavel",
]
for marker in required:
    assert marker in page, f"missing encoded id marker: {marker}"

start = page.index("proposal_id codificado para endpoint de detalhe")
end = page.index("Preview GET detalhe auditavel", start)
encoded_block = page[start:end]
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
    assert forbidden not in encoded_block, f"forbidden token in encoded id block: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-p-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_encoded_id_panel.py"
assert scripts["smoke:phase-p"] == "npm run smoke:phase-p-ui && npm run smoke:phase-o"

for marker in [
    "Phase P",
    "Detail encoded proposal_id UI read-only",
    "proposal_id codificado para endpoint de detalhe",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_encoded_id_panel")
