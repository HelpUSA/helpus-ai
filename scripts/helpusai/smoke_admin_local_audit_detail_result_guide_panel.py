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
    "Guia do resultado do detalhe",
    "found</span>: indica se o proposal_id foi localizado.",
    "proposal</span>: mostra o registro auditavel retornado pelo GET.",
    "executed</span> e <span",
    "approved</span>: devem permanecer false.",
    "Guia read-only: este bloco apenas explica o resultado carregado",
    "Detalhe da proposta",
]
for marker in required:
    assert marker in page, f"missing result guide marker: {marker}"
start = page.index("Guia do resultado do detalhe")
end = page.index("Detalhe da proposta", start)
result_guide_block = page[start:end]
for forbidden in ["fetchLocal", "postLocal", "method: 'POST'", "setProposalDetailId", "/local/execute", "/local/commands", "/local/plan/execute", "/local/plan/run", "/local/plan/approve"]:
    assert forbidden not in result_guide_block, f"forbidden token in result guide block: {forbidden}"
scripts = package["scripts"]
assert scripts["smoke:phase-r-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_result_guide_panel.py"
assert scripts["smoke:phase-r"] == "npm run smoke:phase-r-ui && npm run smoke:phase-q"
for marker in ["Phase R", "Detail result guide UI read-only", "Guia do resultado do detalhe"]:
    assert marker in doc, f"missing doc marker: {marker}"
print("OK smoke_admin_local_audit_detail_result_guide_panel")
