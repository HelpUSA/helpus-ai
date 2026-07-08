from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
page=(ROOT/"frontend/src/app/admin/local/page.tsx").read_text(encoding="utf-8-sig",errors="replace")
pkg=json.loads((ROOT/"package.json").read_text(encoding="utf-8-sig",errors="replace"))
doc=(ROOT/"docs/local-plan-audit.md").read_text(encoding="utf-8-sig",errors="replace")
for m in ["proposal_id detectado automaticamente","findProposalId(proposalResult) || findProposalId(proposals)","Nenhum proposal_id detectado na proposta criada ou na lista.","Hint read-only","Preencher id da proposta criada","Preencher id da lista","Carregar detalhe auditavel"]:
    assert m in page, f"missing marker: {m}"
s=page.index("proposal_id detectado automaticamente")
e=page.index("Preencher id da proposta criada",s)
hint=page[s:e]
for bad in ["fetchLocal","postLocal","method: 'POST'","/local/execute","/local/commands","/local/plan/execute","/local/plan/run","/local/plan/approve","setProposalDetailId"]:
    assert bad not in hint, f"bad token in hint: {bad}"
assert pkg["scripts"]["smoke:phase-l-ui"]=="python scripts/helpusai/smoke_admin_local_audit_detail_detected_id_panel.py"
assert pkg["scripts"]["smoke:phase-l"]=="npm run smoke:phase-l-ui && npm run smoke:phase-k"
for m in ["Phase L","Detected proposal_id hint UI read-only","proposal_id detectado automaticamente"]:
    assert m in doc, f"missing doc marker: {m}"
print("OK smoke_admin_local_audit_detail_detected_id_panel")
