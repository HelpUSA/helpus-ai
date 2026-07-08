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
    "Limite da consulta GET de detalhe",
    "Status, normalizacao, codificacao, checklist e preview sao somente leitura.",
    "A consulta GET de detalhe acontece apenas ao clicar em Carregar detalhe auditavel.",
    "Estes blocos nao criam proposta, nao aprovam nada e nao executam comandos.",
    "Preview GET detalhe auditavel",
    "Carregar detalhe auditavel",
]
for marker in required:
    assert marker in page, f"missing boundary marker: {marker}"

start = page.index("Limite da consulta GET de detalhe")
end = page.index("Preview GET detalhe auditavel", start)
boundary_block = page[start:end]
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
    assert forbidden not in boundary_block, f"forbidden token in boundary block: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-r-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_get_boundary_panel.py"
assert scripts["smoke:phase-r"] == "npm run smoke:phase-r-ui && npm run smoke:phase-q"

for marker in [
    "Phase R",
    "Detail GET boundary UI read-only",
    "Limite da consulta GET de detalhe",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_get_boundary_panel")
