
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

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    HANDOFF,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
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

expected = {
    "smoke:phase-ab-ui":
        "python scripts/52_smoke_handoff_summary_preview.py",
    "smoke:phase-ab":
        "npm run smoke:phase-ab-ui && npm run smoke:phase-aa",
}

for key, value in expected.items():
    actual = package["scripts"].get(key)
    assert actual == value, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "HandoffSummaryPreview",
    "buildHandoffSummaryPreview",
    "formatHandoffSummaryPreview",
    "handoffSummaryPreview",
    "Resumo de handoff multiagente",
    "HANDOFF_START/HANDOFF_END",
    "Repositorio e branch",
    "Fonte do contexto",
    "Risco derivado",
    "Estado do handoff",
    "Arquivos para handoff",
    "Validacao do handoff",
    "Postura de seguranca",
    "Proxima acao segura",
    "Preview HANDOFF_START",
    "Limite de handoff",
    "smoke:phase-ab",
    "smoke:phase-aa",
]:
    assert marker in page, f"missing Phase AB marker: {marker}"

for marker in [
    "Modo de proposta de patch",
    "Matriz de risco estruturado",
    "Capacidades da IA",
]:
    assert marker in page, f"missing previous UI marker: {marker}"

for marker in [
    "Phase AB implementation contract",
    "smoke:phase-ab",
    "52_smoke_handoff_summary_preview.py",
]:
    assert marker in capabilities, marker

for marker in [
    "Admin handoff summary preview after Phase AB",
    "smoke:phase-ab",
]:
    assert marker in handoff, marker

for marker in [
    "Handoff summary preview after Phase AB",
    "smoke:phase-ab",
]:
    assert marker in local_audit, marker

for marker in [
    "Checkpoint Phase AB handoff summary preview",
    "smoke:phase-ab",
]:
    assert marker in status, marker

for marker in [
    "Phase AB handoff summary preview",
    "smoke:phase-ab",
]:
    assert marker in roadmap, marker

print("SMOKE_HANDOFF_SUMMARY_PREVIEW_OK")
