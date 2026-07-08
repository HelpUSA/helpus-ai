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
    "Checklist GET detalhe auditavel",
    "Confirme o proposal_id normalizado.",
    "Confira o proposal_id codificado.",
    "Revise o Preview GET detalhe auditavel.",
    "Clique em Carregar detalhe auditavel somente quando quiser consultar.",
    "Checklist read-only: este bloco nao chama API",
    "Preview GET detalhe auditavel",
    "Carregar detalhe auditavel",
]
for marker in required:
    assert marker in page, f"missing checklist marker: {marker}"

start = page.index("Checklist GET detalhe auditavel")
end = page.index("Preview GET detalhe auditavel", start)
checklist_block = page[start:end]
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
    assert forbidden not in checklist_block, f"forbidden token in checklist block: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-q-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_get_checklist_panel.py"
assert scripts["smoke:phase-q"] == "npm run smoke:phase-q-ui && npm run smoke:phase-p"

for marker in [
    "Phase Q",
    "Detail GET checklist UI read-only",
    "Checklist GET detalhe auditavel",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_get_checklist_panel")
