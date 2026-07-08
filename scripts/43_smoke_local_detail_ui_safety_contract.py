from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
DOC = ROOT / "docs/local-plan-audit.md"

page = PAGE.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(PACKAGE.read_text(encoding="utf-8-sig", errors="replace"))
doc = DOC.read_text(encoding="utf-8-sig", errors="replace")

required_page_markers = [
    "Detalhe da proposta",
    "Carregar detalhe auditavel",
    "GET /local/plan/proposals/{proposal_id}",
    "proposal_id detectado automaticamente",
    "proposal_id normalizado para detalhe",
    "proposal_id codificado para endpoint de detalhe",
    "Status do proposal_id para detalhe",
    "Checklist GET detalhe auditavel",
    "Limite da consulta GET de detalhe",
    "Contrato GET detalhe auditavel",
]
for marker in required_page_markers:
    assert marker in page, f"missing detail safety marker: {marker}"

labels = [
    "Status do proposal_id para detalhe",
    "proposal_id normalizado para detalhe",
    "proposal_id codificado para endpoint de detalhe",
    "Checklist GET detalhe auditavel",
    "Limite da consulta GET de detalhe",
    "Preview GET detalhe auditavel",
    "Contrato GET detalhe auditavel",
]
forbidden = [
    "postLocal",
    "method: 'POST'",
    'method: "POST"',
    "setProposalDetailId",
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
]
positions = {label: page.index(label) for label in labels if label in page}
for label, start in positions.items():
    next_positions = [pos for other, pos in positions.items() if pos > start]
    end = min(next_positions) if next_positions else start + 2200
    block = page[start:end]
    for token in forbidden:
        assert token not in block, f"forbidden token in read-only detail safety block {label}: {token}"

scripts = package["scripts"]
assert scripts["smoke:phase-s-detail-safety"] == "python scripts/43_smoke_local_detail_ui_safety_contract.py"
assert scripts["smoke:phase-s"] == "npm run smoke:phase-s-detail-safety && npm run smoke:phase-r"

for marker in [
    "Phase S",
    "Detail safety aggregate smoke",
    "43_smoke_local_detail_ui_safety_contract.py",
]:
    assert marker in doc, f"missing doc marker: {marker}"

print("SMOKE_LOCAL_DETAIL_UI_SAFETY_CONTRACT_OK")
