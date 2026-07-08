from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[2]
page = (ROOT / "frontend/src/app/admin/local/page.tsx").read_text(encoding="utf-8-sig", errors="replace")
package = json.loads((ROOT / "package.json").read_text(encoding="utf-8-sig", errors="replace"))
doc = (ROOT / "docs/local-plan-audit.md").read_text(encoding="utf-8-sig", errors="replace")
for marker in ["proposalDetailId","setProposalDetailId","proposalDetail","setProposalDetail","carregarDetalheProposta","proposal_id para detalhe auditavel","Carregar detalhe auditavel","Detalhe da proposta","GET /local/plan/proposals/{proposal_id}","/local/plan/proposals/${encodeURIComponent(normalized)}"]:
    assert marker in page, f"missing marker: {marker}"
fn = page[page.index("const carregarDetalheProposta"):page.index("  return (", page.index("const carregarDetalheProposta"))]
assert "fetchLocal<unknown>" in fn
assert "postLocal" not in fn
assert "method: 'POST'" not in fn
assert package["scripts"]["smoke:phase-j-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_panel.py"
assert package["scripts"]["smoke:phase-j"] == "npm run smoke:phase-j-ui && npm run smoke:phase-i"
for marker in ["Phase J","Detail UI read-only","GET /local/plan/proposals/{proposal_id}","Carregar detalhe auditavel"]:
    assert marker in doc, f"missing doc marker: {marker}"
print("OK smoke_admin_local_audit_detail_panel")
