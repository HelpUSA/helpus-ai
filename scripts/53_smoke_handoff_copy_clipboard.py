
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
SMOKE_52 = ROOT / "scripts/52_smoke_handoff_summary_preview.py"

for required in [
    PAGE,
    PACKAGE,
    CAPABILITIES,
    HANDOFF,
    LOCAL_AUDIT,
    STATUS,
    ROADMAP,
    SMOKE_52,
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
    "smoke:phase-ac-ui":
        "python scripts/53_smoke_handoff_copy_clipboard.py",
    "smoke:phase-ac":
        "npm run smoke:phase-ac-ui && npm run smoke:phase-ab",
}

for key, expected in expected_scripts.items():
    actual = package["scripts"].get(key)

    assert actual == expected, (
        f"unexpected package script {key}: {actual!r}"
    )

for marker in [
    "handoffCopyStatus",
    "setHandoffCopyStatus",
    "copiarResumoHandoff",
    "navigator.clipboard.writeText",
    "clipboard_unavailable",
    "Copiar handoff",
    "Handoff copiado para a area de transferencia.",
    "Copia automatica indisponivel.",
    "onClick={() => void copiarResumoHandoff()}",
    "Copiar nao transmite nem executa o handoff.",
    "smoke:phase-ac",
    "smoke:phase-ab",
]:
    assert marker in page, (
        f"missing Phase AC page marker: {marker}"
    )

for marker in [
    "Resumo de handoff multiagente",
    "Modo de proposta de patch",
    "Matriz de risco estruturado",
    "Capacidades da IA",
]:
    assert marker in page, (
        f"missing previous UI marker: {marker}"
    )

for marker in [
    "Phase AC implementation contract",
    "smoke:phase-ac",
    "53_smoke_handoff_copy_clipboard.py",
]:
    assert marker in capabilities, (
        f"missing capabilities marker: {marker}"
    )

for marker in [
    "Copy-to-clipboard after Phase AC",
    "smoke:phase-ac",
]:
    assert marker in handoff, (
        f"missing handoff marker: {marker}"
    )

for marker in [
    "Handoff copy support after Phase AC",
    "smoke:phase-ac",
]:
    assert marker in local_audit, (
        f"missing local audit marker: {marker}"
    )

for marker in [
    "Checkpoint Phase AC handoff copy support",
    "smoke:phase-ac",
]:
    assert marker in status, (
        f"missing status marker: {marker}"
    )

for marker in [
    "Phase AC handoff copy support",
    "smoke:phase-ac",
]:
    assert marker in roadmap, (
        f"missing roadmap marker: {marker}"
    )

assert page.count(
    "onClick={() => void copiarResumoHandoff()}"
) == 1, "copy action must require exactly one explicit click"

print("SMOKE_HANDOFF_COPY_CLIPBOARD_OK")
