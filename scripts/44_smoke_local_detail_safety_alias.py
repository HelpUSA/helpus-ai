from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
DOC = ROOT / "docs/local-plan-audit.md"
AGGREGATE = ROOT / "scripts/43_smoke_local_detail_ui_safety_contract.py"
EXECUTOR_GUARD = ROOT / "scripts/38_smoke_local_executor_absent.py"

page = PAGE.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(PACKAGE.read_text(encoding="utf-8-sig", errors="replace"))
doc = DOC.read_text(encoding="utf-8-sig", errors="replace")

assert AGGREGATE.exists(), "missing aggregate detail safety smoke"
assert EXECUTOR_GUARD.exists(), "missing executor absence smoke"

scripts = package["scripts"]
assert scripts["smoke:local-detail-safety"] == "npm run smoke:phase-s-detail-safety && python scripts/38_smoke_local_executor_absent.py"
assert scripts["smoke:phase-t-alias"] == "python scripts/44_smoke_local_detail_safety_alias.py"
assert scripts["smoke:phase-t"] == "npm run smoke:phase-t-alias && npm run smoke:local-detail-safety && npm run smoke:phase-s"

for marker in [
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
]:
    assert marker in page, f"missing detail UI marker: {marker}"

for marker in [
    "Phase T",
    "Detail safety smoke alias",
    "smoke:local-detail-safety",
    "44_smoke_local_detail_safety_alias.py",
]:
    assert marker in doc, f"missing doc marker: {marker}"

for forbidden in [
    "/local/execute",
    "/local/commands",
    "/local/plan/execute",
    "/local/plan/run",
    "/local/plan/approve",
    '"approved": True',
    "'approved': True",
    "approved = True",
    '"executed": True',
    "'executed': True",
    "executed = True",
]:
    assert forbidden not in page, f"forbidden token in admin local page: {forbidden}"

print("SMOKE_LOCAL_DETAIL_SAFETY_ALIAS_OK")
