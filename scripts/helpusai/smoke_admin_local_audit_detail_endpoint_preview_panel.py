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
    "Preview GET detalhe auditavel",
    "proposalDetailId.trim()",
    "`/local/plan/proposals/${encodeURIComponent(proposalDetailId.trim())}`",
    "'/local/plan/proposals/{proposal_id}'",
    "Preview read-only: nao chama API automaticamente",
    "Carregar detalhe auditavel",
]
for marker in required:
    assert marker in page, f"missing endpoint preview marker: {marker}"

start = page.index("Preview GET detalhe auditavel")
end = page.index("Carregar detalhe auditavel", start)
preview = page[start:end]
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
    assert forbidden not in preview, f"forbidden token in endpoint preview: {forbidden}"

scripts = package["scripts"]
assert scripts["smoke:phase-m-ui"] == "python scripts/helpusai/smoke_admin_local_audit_detail_endpoint_preview_panel.py"
assert scripts["smoke:phase-m"] == "npm run smoke:phase-m-ui && npm run smoke:phase-l"

for marker in [
    "Phase M",
    "Endpoint preview UI read-only",
    "Preview GET detalhe auditavel",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("OK smoke_admin_local_audit_detail_endpoint_preview_panel")
