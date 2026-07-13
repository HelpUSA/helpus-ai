
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
HANDOFF = ROOT / "docs/ai/MULTI_AGENT_HANDOFF.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"

SMOKE_56 = ROOT / "scripts/56_smoke_ci_phase_ae_chain.py"
SMOKE_55 = ROOT / "scripts/55_smoke_handoff_download.py"
SMOKE_54 = ROOT / "scripts/54_smoke_ci_phase_ac_chain.py"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    HANDOFF,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_56,
    SMOKE_55,
    SMOKE_54,
]:
    assert required.exists(), f"missing required file: {required}"

page = PAGE.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

package = json.loads(
    PACKAGE.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )
)

capabilities = CAPABILITIES.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

handoff = HANDOFF.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

local_audit = LOCAL_AUDIT.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

status = STATUS.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

roadmap = ROADMAP.read_text(
    encoding="utf-8-sig",
    errors="replace",
)

expected_scripts = {
    "smoke:phase-ag-ui":
        "python scripts/57_smoke_handoff_readiness_checklist.py",
    "smoke:phase-ag":
        "npm run smoke:phase-ag-ui && npm run smoke:phase-af",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "HandoffReadinessItem",
    "HandoffReadinessSummary",
    "buildHandoffReadinessChecklist",
    "summarizeHandoffReadiness",
    "handoffReadinessChecklist",
    "handoffReadinessSummary",
    "Checklist de prontidao do handoff",
    "Campos validos",
    "Repositorio identificado",
    "Branch identificada",
    "Fonte de contexto carregada",
    "Arquivos declarados",
    "Cadeia de validacao declarada",
    "Risco estruturado disponivel",
    "Postura de seguranca preservada",
    "Proxima acao segura definida",
    "Rollback definido",
    "handoff_pronto_para_revisao",
    "handoff_requer_atencao",
    "Requer atencao",
    "Resultado informativo",
    "smoke:phase-ag",
    "smoke:phase-af",
]:
    assert marker in page, (
        f"missing Phase AG page marker: {marker}"
    )

for marker in [
    "Baixar .txt",
    "Copiar handoff",
    "Resumo de handoff multiagente",
    "Modo de proposta de patch",
    "Matriz de risco estruturado",
    "Capacidades da IA",
]:
    assert marker in page, (
        f"missing previous UI marker: {marker}"
    )

for marker in [
    "Phase AG implementation contract",
    "smoke:phase-ag",
    "57_smoke_handoff_readiness_checklist.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Readiness checklist after Phase AG",
    "smoke:phase-ag",
]:
    assert marker in handoff, marker

for marker in [
    "Handoff readiness after Phase AG",
    "smoke:phase-ag",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AG handoff readiness",
    "smoke:phase-ag",
]:
    assert marker in status, marker

for marker in [
    "Phase AG handoff readiness checklist",
    "smoke:phase-ag",
]:
    assert marker in roadmap, marker

assert page.count(
    "handoffReadinessChecklist.map"
) == 1, "readiness checklist must render exactly once"

assert "approved = True" not in page
assert '"approved": True' not in page
assert "'approved': True" not in page
assert "executed = True" not in page
assert '"executed": True' not in page
assert "'executed': True" not in page

print("SMOKE_HANDOFF_READINESS_CHECKLIST_OK")
