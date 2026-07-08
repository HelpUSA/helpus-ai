from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
DOC = ROOT / "docs/local-plan-audit.md"

page = PAGE.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(PACKAGE.read_text(encoding="utf-8-sig", errors="replace"))
doc = DOC.read_text(encoding="utf-8-sig", errors="replace")

for marker in [
    "function findProposalId",
    "const usarPropostaIdAuditavel",
    "setProposalDetailId(id)",
    "Nenhum proposal_id encontrado para preencher o detalhe auditavel.",
    "Preencher id da proposta criada",
    "Preencher id da lista",
    "findProposalId(proposalResult)",
    "findProposalId(proposals)",
    "Carregar detalhe auditavel",
    "Detalhe da proposta",
]:
    assert marker in page, f"missing quickfill marker: {marker}"

quick_start = page.index("const usarPropostaIdAuditavel")
quick_end = page.index("const carregarDetalheProposta", quick_start)
quick_fn = page[quick_start:quick_end]
assert "findProposalId(source)" in quick_fn
assert "setProposalDetailId(id)" in quick_fn
assert "postLocal" not in quick_fn
assert "method: 'POST'" not in quick_fn

helper = page[page.index("function findProposalId"):page.index("function RiskBadge")]
assert "record.proposal_id" in helper
assert "record.proposal" in helper
assert "record.proposals" in helper
assert "Array.isArray(proposals)" in helper

for forbidden in ["/local/execute", "/local/commands", "/local/plan/execute", "/local/plan/run", "/local/plan/approve"]:
    assert forbidden not in quick_fn, f"forbidden endpoint in quickfill function: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-k-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_quickfill_panel.py"
assert scripts["smoke:phase-k"] == "npm run smoke:phase-k-ui && npm run smoke:phase-j"

for marker in [
    "Phase K",
    "Detail quick-fill UI read-only",
    "Preencher id da proposta criada",
    "Preencher id da lista",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_quickfill_panel")
