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
    "Contrato GET detalhe auditavel",
    "Endpoint permitido: GET /local/plan/proposals/[proposal_id].",
    "Consulta somente leitura: nao cria, nao aprova e nao executa propostas.",
    "Resultado exibido apenas apos clicar em Carregar detalhe auditavel.",
    "Carregar detalhe auditavel",
    "Detalhe da proposta",
]
for marker in required:
    assert marker in page, f"missing detail get contract marker: {marker}"

start = page.index("Contrato GET detalhe auditavel")
end = page.index("Detalhe da proposta", start)
contract_block = page[start:end]
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
    assert forbidden not in contract_block, f"forbidden token in detail get contract block: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-r-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_get_contract_panel.py"
assert scripts["smoke:phase-r"] == "npm run smoke:phase-r-ui && npm run smoke:phase-q"

for marker in [
    "Phase R",
    "Detail GET contract UI read-only",
    "Contrato GET detalhe auditavel",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_get_contract_panel")
