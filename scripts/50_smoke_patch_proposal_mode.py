
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

PAGE = ROOT / "frontend/src/app/admin/local/page.tsx"
PACKAGE = ROOT / "package.json"
CAPABILITIES = ROOT / "docs/ai/CAPABILITIES_AND_NEXT_STEPS.md"
LOCAL_AUDIT = ROOT / "docs/local-plan-audit.md"
STATUS = ROOT / "docs/obsidian/HELPUSAI_STATUS_2026-07-06.md"
ROADMAP = ROOT / "docs/obsidian/HELPUSAI_ROADMAP_OBSIDIAN.md"
HANDOFF = ROOT / "docs/ai/MULTI_AGENT_HANDOFF.md"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    HANDOFF,
]:
    assert required.exists(), f"missing required file: {required}"

page = PAGE.read_text(encoding="utf-8-sig", errors="replace")
package = json.loads(
    PACKAGE.read_text(encoding="utf-8-sig", errors="replace")
)
capabilities = CAPABILITIES.read_text(
    encoding="utf-8-sig",
    errors="replace",
)
local_audit = LOCAL_AUDIT.read_text(
    encoding="utf-8-sig",
    errors="replace",
)
status = STATUS.read_text(encoding="utf-8-sig", errors="replace")
roadmap = ROADMAP.read_text(encoding="utf-8-sig", errors="replace")
handoff = HANDOFF.read_text(encoding="utf-8-sig", errors="replace")

expected = {
    "smoke:phase-z-ui":
        "python scripts/50_smoke_patch_proposal_mode.py",
    "smoke:phase-z":
        "npm run smoke:phase-z-ui && npm run smoke:phase-y",
}

for key, value in expected.items():
    assert package["scripts"].get(key) == value, key

for marker in [
    "PatchProposalPreview",
    "buildPatchProposalPreview",
    "patchProposalPreview",
    "Modo de proposta de patch",
    "proposal_only",
    "Status da proposta",
    "Fonte",
    "Arquivos declarados",
    "Validacoes obrigatorias",
    "Objetivo proposto",
    "Rollback sugerido",
    "Preview auditavel",
    "Limite de seguranca",
    "nao aplica patch",
    "nao cria commit",
    "nao faz push",
    "nao executa comandos",
    "smoke:phase-z",
    "smoke:phase-y",
    "smoke:local-audit-safety",
]:
    assert marker in page, f"missing page marker: {marker}"

for marker in [
    "Capacidades da IA",
    "Matriz de risco estruturado",
    "Detalhe da proposta",
]:
    assert marker in page, f"missing previous UI marker: {marker}"

for marker in [
    "Phase Z implementation contract",
    "smoke:phase-z",
    "50_smoke_patch_proposal_mode.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Patch proposal mode after Phase Z",
    "smoke:phase-z",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase Z patch proposal mode",
    "smoke:phase-z",
]:
    assert marker in status, marker

for marker in [
    "Phase Z patch proposal mode",
    "smoke:phase-z",
]:
    assert marker in roadmap, marker

for marker in [
    "Phase Z patch proposal mode",
    "rollback",
    "safety_posture",
]:
    assert marker in handoff, marker

print("SMOKE_PATCH_PROPOSAL_MODE_OK")
